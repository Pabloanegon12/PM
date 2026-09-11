import json
import os

import httpx2

from app.schemas import Board, ChatMessage

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nvidia/nemotron-3.5-lightning:free"

OPERATIONS_HELP = (
    "- create_card: columnId, title, details\n"
    "- update_card: cardId, title, details\n"
    "- delete_card: cardId\n"
    "- rename_column: columnId, name\n"
    "- move_card: cardId, toColumnId, toIndex"
)

CHAT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "message": {"type": "string"},
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "op": {
                        "type": "string",
                        "enum": [
                            "create_card",
                            "update_card",
                            "delete_card",
                            "rename_column",
                            "move_card",
                        ],
                    },
                    "columnId": {"type": ["string", "null"]},
                    "cardId": {"type": ["string", "null"]},
                    "title": {"type": ["string", "null"]},
                    "details": {"type": ["string", "null"]},
                    "name": {"type": ["string", "null"]},
                    "toColumnId": {"type": ["string", "null"]},
                    "toIndex": {"type": ["integer", "null"]},
                },
                "required": [
                    "op",
                    "columnId",
                    "cardId",
                    "title",
                    "details",
                    "name",
                    "toColumnId",
                    "toIndex",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["message", "operations"],
    "additionalProperties": False,
}


class AIError(Exception):
    pass


async def _post(payload: dict, timeout: float = 60) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise AIError("OPENROUTER_API_KEY no está configurada")

    try:
        async with httpx2.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": MODEL, **payload},
            )
        response.raise_for_status()
    except httpx2.HTTPError as error:
        raise AIError(f"Fallo al llamar a OpenRouter: {error}") from error

    return response.json()


async def ask(prompt: str) -> str:
    data = await _post({"messages": [{"role": "user", "content": prompt}]})
    return data["choices"][0]["message"]["content"]


async def chat(board: Board, history: list[ChatMessage], user_message: str) -> dict:
    system_prompt = (
        "Eres un asistente que ayuda a gestionar un tablero Kanban. Responde siempre en español.\n"
        "Este es el estado actual del tablero en JSON (usa los ids de columnas y tarjetas tal cual "
        "aparecen aquí, no inventes otros):\n"
        f"{board.model_dump_json()}\n\n"
        "Puedes responder al usuario y, opcionalmente, proponer cambios al tablero mediante una lista "
        f"de operaciones. Operaciones disponibles:\n{OPERATIONS_HELP}\n"
        "Si no hace falta cambiar el tablero, devuelve una lista de operaciones vacía."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages += [{"role": entry.role, "content": entry.content} for entry in history]
    messages.append({"role": "user", "content": user_message})

    data = await _post(
        {
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "kanban_response",
                    "strict": True,
                    "schema": CHAT_RESPONSE_SCHEMA,
                },
            },
        },
        timeout=120,
    )

    content = data["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        raise AIError("La IA no devolvió contenido en la respuesta")
    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise AIError("La IA devolvió una respuesta que no es JSON válido") from error
