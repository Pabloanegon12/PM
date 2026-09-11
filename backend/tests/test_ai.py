import asyncio
import json

import httpx2
import pytest
from fastapi.testclient import TestClient

from app import ai
from app.main import app
from app.schemas import Board, Column


class _FakeAsyncClient:
    def __init__(self, post_fn, **_kwargs):
        self._post_fn = post_fn

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, **kwargs):
        result = self._post_fn(url, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result


def _mock_async_client(monkeypatch: pytest.MonkeyPatch, post_fn):
    monkeypatch.setattr(ai.httpx2, "AsyncClient", lambda **kwargs: _FakeAsyncClient(post_fn, **kwargs))


def test_ask_returns_the_ai_content(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_post(url, **kwargs):
        assert url == ai.OPENROUTER_URL
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        assert kwargs["json"]["model"] == ai.MODEL
        return httpx2.Response(
            200,
            json={"choices": [{"message": {"content": "4"}}]},
            request=httpx2.Request("POST", url),
        )

    _mock_async_client(monkeypatch, fake_post)

    assert asyncio.run(ai.ask("2+2")) == "4"


def test_ask_raises_without_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ai.AIError):
        asyncio.run(ai.ask("2+2"))


def test_ask_raises_on_http_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_post(url, **kwargs):
        return httpx2.Response(
            401, json={"error": "invalid key"}, request=httpx2.Request("POST", url)
        )

    _mock_async_client(monkeypatch, fake_post)

    with pytest.raises(ai.AIError):
        asyncio.run(ai.ask("2+2"))


def test_ask_raises_on_network_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_post(url, **kwargs):
        raise httpx2.ConnectError("connection refused")

    _mock_async_client(monkeypatch, fake_post)

    with pytest.raises(ai.AIError):
        asyncio.run(ai.ask("2+2"))


def test_post_raises_when_response_trickles_past_the_total_timeout(monkeypatch: pytest.MonkeyPatch):
    # Regression test: httpx2's `timeout` only bounds the gap between reads, not the
    # total request duration, so a response that keeps the connection alive without
    # ever completing (as OpenRouter does while a reasoning model "thinks") would
    # hang forever. `ai._post` must enforce a real overall deadline.
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    async def fake_post(url, **kwargs):
        await asyncio.sleep(10)
        return httpx2.Response(200, json={}, request=httpx2.Request("POST", url))

    _mock_async_client(monkeypatch, fake_post)

    with pytest.raises(ai.AIError):
        asyncio.run(ai._post({"messages": []}, timeout=0.05))


def test_ai_test_endpoint_requires_session(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "ai.db"))
    with TestClient(app) as client:
        response = client.post("/api/ai/test")
    assert response.status_code == 401


def test_ai_test_endpoint_returns_the_answer(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "ai.db"))

    async def fake_ask(prompt: str) -> str:
        return "4"

    monkeypatch.setattr(ai, "ask", fake_ask)

    with TestClient(app) as client:
        client.post("/api/login", json={"username": "user", "password": "password"})
        response = client.post("/api/ai/test")

    assert response.status_code == 200
    assert response.json() == {"answer": "4"}


def test_ai_test_endpoint_returns_502_on_ai_error(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "ai.db"))

    async def raise_error(prompt: str) -> str:
        raise ai.AIError("boom")

    monkeypatch.setattr(ai, "ask", raise_error)

    with TestClient(app) as client:
        client.post("/api/login", json={"username": "user", "password": "password"})
        response = client.post("/api/ai/test")

    assert response.status_code == 502


def test_chat_sends_board_and_history_and_parses_structured_response(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    captured = {}

    def fake_post(url, **kwargs):
        captured["json"] = kwargs["json"]
        content = json.dumps({"message": "Hola", "operations": []})
        return httpx2.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
            request=httpx2.Request("POST", url),
        )

    _mock_async_client(monkeypatch, fake_post)

    example_board = Board(columns=[Column(id="1", name="Backlog", cardIds=[])], cards={})
    result = asyncio.run(ai.chat(example_board, [], "hola"))

    assert result == {"message": "Hola", "operations": []}
    sent_messages = captured["json"]["messages"]
    assert sent_messages[0]["role"] == "system"
    assert '"Backlog"' in sent_messages[0]["content"]
    assert sent_messages[-1] == {"role": "user", "content": "hola"}
    assert captured["json"]["response_format"]["json_schema"]["strict"] is True


def test_chat_raises_on_non_json_content(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_post(url, **kwargs):
        return httpx2.Response(
            200,
            json={"choices": [{"message": {"content": "esto no es json"}}]},
            request=httpx2.Request("POST", url),
        )

    _mock_async_client(monkeypatch, fake_post)

    example_board = Board(columns=[], cards={})
    with pytest.raises(ai.AIError):
        asyncio.run(ai.chat(example_board, [], "hola"))


def test_chat_raises_when_content_is_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fake_post(url, **kwargs):
        return httpx2.Response(
            200,
            json={"choices": [{"message": {"content": None}}]},
            request=httpx2.Request("POST", url),
        )

    _mock_async_client(monkeypatch, fake_post)

    example_board = Board(columns=[], cards={})
    with pytest.raises(ai.AIError):
        asyncio.run(ai.chat(example_board, [], "hola"))


def test_ai_chat_endpoint_requires_session(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "chat1.db"))
    with TestClient(app) as client:
        response = client.post("/api/ai/chat", json={"message": "hola"})
    assert response.status_code == 401


def test_ai_chat_endpoint_text_only(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "chat2.db"))

    async def fake_chat(board, history, message):
        return {"message": "Hola", "operations": []}

    monkeypatch.setattr(ai, "chat", fake_chat)

    with TestClient(app) as client:
        client.post("/api/login", json={"username": "user", "password": "password"})
        response = client.post("/api/ai/chat", json={"message": "hola"})

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hola"
    assert len(data["board"]["columns"]) == 5


def test_ai_chat_endpoint_applies_valid_operation_and_persists(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "chat3.db"))

    async def fake_chat(board, history, message):
        column_id = board.columns[0].id
        return {
            "message": "Tarjeta creada",
            "operations": [
                {
                    "op": "create_card",
                    "columnId": column_id,
                    "title": "Nueva de la IA",
                    "details": "Creada por la IA",
                    "cardId": None,
                    "name": None,
                    "toColumnId": None,
                    "toIndex": None,
                }
            ],
        }

    monkeypatch.setattr(ai, "chat", fake_chat)

    with TestClient(app) as client:
        client.post("/api/login", json={"username": "user", "password": "password"})
        response = client.post("/api/ai/chat", json={"message": "crea una tarjeta"})
        assert response.status_code == 200
        assert any(
            card["title"] == "Nueva de la IA" for card in response.json()["board"]["cards"].values()
        )

        board_response = client.get("/api/board")
        assert any(
            card["title"] == "Nueva de la IA" for card in board_response.json()["cards"].values()
        )


def test_ai_chat_endpoint_rejects_invalid_operation_with_cause(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "chat4.db"))

    async def fake_chat(board, history, message):
        return {
            "message": "Movida",
            "operations": [
                {
                    "op": "move_card",
                    "cardId": "9999",
                    "toColumnId": board.columns[0].id,
                    "toIndex": 0,
                    "columnId": None,
                    "title": None,
                    "details": None,
                    "name": None,
                }
            ],
        }

    monkeypatch.setattr(ai, "chat", fake_chat)

    with TestClient(app) as client:
        client.post("/api/login", json={"username": "user", "password": "password"})
        response = client.post("/api/ai/chat", json={"message": "mueve algo inexistente"})

    assert response.status_code == 422
    assert "no encontrada" in response.json()["detail"].lower()


def test_ai_chat_endpoint_returns_422_on_malformed_ai_operation(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    # Regression test: a structured-output response that doesn't match AIOperation's
    # shape (the free model doesn't guarantee 100% schema adherence) must surface as
    # a clean 422, not an unhandled 500.
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "chat6.db"))

    async def fake_chat(board, history, message):
        return {"message": "ok", "operations": [{"op": "not_a_real_operation"}]}

    monkeypatch.setattr(ai, "chat", fake_chat)

    with TestClient(app) as client:
        client.post("/api/login", json={"username": "user", "password": "password"})
        response = client.post("/api/ai/chat", json={"message": "hola"})

    assert response.status_code == 422


def test_ai_chat_endpoint_does_not_partially_apply_an_invalid_batch(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    # Regression test: if the AI proposes several operations and a later one is
    # invalid, none of them should be persisted — previously each operation
    # committed its own transaction, so the first one stuck even though the whole
    # request reported an error.
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "chat7.db"))

    async def fake_chat(board, history, message):
        column_id = board.columns[0].id
        return {
            "message": "Dos operaciones",
            "operations": [
                {
                    "op": "create_card",
                    "columnId": column_id,
                    "title": "No deberia persistir",
                    "details": "",
                    "cardId": None,
                    "name": None,
                    "toColumnId": None,
                    "toIndex": None,
                },
                {
                    "op": "delete_card",
                    "cardId": "9999",
                    "columnId": None,
                    "title": None,
                    "details": None,
                    "name": None,
                    "toColumnId": None,
                    "toIndex": None,
                },
            ],
        }

    monkeypatch.setattr(ai, "chat", fake_chat)

    with TestClient(app) as client:
        client.post("/api/login", json={"username": "user", "password": "password"})
        response = client.post("/api/ai/chat", json={"message": "dos cambios, uno invalido"})
        assert response.status_code == 422

        board_response = client.get("/api/board")
        assert not any(
            card["title"] == "No deberia persistir"
            for card in board_response.json()["cards"].values()
        )


def test_ai_chat_endpoint_persists_conversation_history_per_session(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "chat5.db"))
    received_histories = []

    async def fake_chat(board, history, message):
        received_histories.append(list(history))
        return {"message": f"respuesta a {message}", "operations": []}

    monkeypatch.setattr(ai, "chat", fake_chat)

    with TestClient(app) as client:
        client.post("/api/login", json={"username": "user", "password": "password"})
        client.post("/api/ai/chat", json={"message": "primero"})
        client.post("/api/ai/chat", json={"message": "segundo"})

    assert received_histories[0] == []
    assert len(received_histories[1]) == 2
    assert received_histories[1][0].content == "primero"
    assert received_histories[1][1].content == "respuesta a primero"
