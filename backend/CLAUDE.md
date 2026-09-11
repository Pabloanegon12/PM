# Backend

FastAPI + `uv`, empaquetado en el `Dockerfile` de la raíz del proyecto.

## Estructura

- `pyproject.toml`: dependencias gestionadas con `uv` (`fastapi`, `uvicorn`, `httpx2`; grupo `dev` con `pytest`).
- `app/main.py`: aplicación FastAPI. Rutas de salud, login/logout/sesión y del tablero Kanban; monta `app/static/` en `/` (sirve el build del frontend).
- `app/static/`: estático servido en `/`. En local (sin Docker) contiene el placeholder de la Parte 2; en la imagen Docker se sustituye por el build real del frontend (Parte 3).
- `app/auth.py`: sesión en memoria mediante cookie `httponly` (`session_id`) y credenciales hardcodeadas (`user`/`password`). Expone `require_session` como dependencia para proteger rutas.
- `app/db.py`: conexión SQLite (stdlib `sqlite3`, sin ORM) y creación automática del esquema (`init_db`, ejecutado en el `lifespan` de la app). Ruta configurable con la variable de entorno `PM_DB_PATH` (por defecto `backend/data/pm.db`, útil para aislar tests).
- `app/schemas.py`: modelos Pydantic de entrada/salida de la API (`Board`, `Column`, `Card` y los payloads de cada mutación), con nombres de campo en camelCase para que coincidan con el contrato que ya usa el frontend.
- `app/board.py`: capa de acceso a datos del tablero (siembra inicial, lectura y mutaciones — crear/editar/eliminar tarjeta, renombrar columna, mover tarjeta). El orden de columnas y tarjetas se guarda como un entero `position` por fila; mover una tarjeta reindexa las columnas de origen y destino.
- `app/ai.py`: cliente HTTP hacia OpenRouter (`httpx2.AsyncClient`, asíncrono — ver nota sobre `httpx2` más abajo) con el modelo `nvidia/nemotron-3.5-lightning:free`. `ask(prompt)` es la llamada simple de prueba; `chat(board, history, user_message)` construye el prompt de sistema con el tablero completo en JSON y el historial, y pide **Structured Outputs** (`response_format: json_schema`, modo `strict`) con forma `{"message": str, "operations": [...]}`. Lanza `AIError` si falta la clave, si la llamada HTTP falla, o si la IA no devuelve JSON válido.
- `app/chat.py`: historial de conversación en memoria, indexado por `session_id` (mismo patrón que las sesiones de `app/auth.py`); se limpia al hacer logout.

## Rutas de la API

- `GET /api/health`
- `POST /api/login`, `POST /api/logout`, `GET /api/me`
- `GET /api/board` — devuelve el tablero del usuario autenticado (lo crea con datos semilla la primera vez).
- `POST /api/board/cards`, `PATCH /api/board/cards/{id}`, `DELETE /api/board/cards/{id}`
- `PATCH /api/board/columns/{id}`
- `POST /api/board/cards/{id}/move`
- `POST /api/ai/test` — envía una pregunta fija ("¿Cuánto es 2+2?") a OpenRouter y devuelve `{"answer": "..."}"`; 502 si falla la llamada a la IA.
- `POST /api/ai/chat` — recibe `{"message": "..."}"`, llama a la IA con el tablero completo + historial de la sesión, aplica las operaciones válidas que proponga (`create_card`, `update_card`, `delete_card`, `rename_column`, `move_card`, reutilizando las funciones de `app/board.py`) y devuelve `{"message": "...", "board": {...}}` con el tablero ya actualizado. 401 sin sesión, 502 si falla la IA, 422 si alguna operación propuesta es inválida (columna/tarjeta inexistente, faltan campos requeridos para ese tipo de operación).

Todas las rutas de `/api/board*` y `/api/ai/*` requieren sesión activa (401 si no la hay) y las de `/api/board*` (y `/api/ai/chat`) devuelven el tablero completo actualizado tras cada mutación.

### Nota sobre `httpx2` y rutas asíncronas

`httpx2.post()` (la función síncrona de conveniencia) se cuelga indefinidamente si se ejecuta en un hilo de threadpool mientras hay un *event loop* de asyncio corriendo en el proceso — exactamente la situación de cualquier ruta FastAPI, aunque sea `def` síncrona (FastAPI la ejecuta en un threadpool con el loop de uvicorn activo en el hilo principal). Por eso `app/ai.py` usa `httpx2.AsyncClient` con `await` y las rutas `/api/ai/*` son `async def`. Como consecuencia, `POST /api/ai/chat` no puede depender de la conexión SQLite compartida vía `Depends(require_board)` (esa conexión se crearía en un hilo distinto al que ejecuta el resto de la ruta async, y sqlite3 prohíbe usar una conexión fuera de su hilo de creación): en su lugar abre su propia conexión de corta vida dentro de cada `run_in_threadpool` (ver `_load_board_for_ai` / `_apply_ai_operations` en `app/main.py`). Las demás rutas (`/api/board*`), al ser totalmente síncronas, no tienen este problema y siguen usando `Depends(require_board)` con normalidad.

### Cada mutación debe confirmar su propia transacción (`connection.commit()`)

`add_card`, `update_card`, `delete_card`, `rename_column` y `move_card` (en `app/board.py`) abren y confirman su propia transacción cada una. Esto importa porque el JSON que devuelve cada ruta se genera con `fetch_board` sobre la **misma conexión** que acaba de escribir, así que refleja el cambio aunque no se haya confirmado todavía — un `commit()` que falte no se nota en la respuesta de esa misma petición, solo se hace evidente al leer con una conexión nueva (la siguiente petición HTTP). Esto pasó de verdad: al añadir `apply_ai_operation` en la Parte 9 se perdió el `connection.commit()` de `move_card`, y ni los tests (que solo comprobaban la respuesta inmediata del propio `move`) ni las pruebas manuales puntuales lo detectaron — hizo falta una prueba e2e con recarga de página (Parte 10) para verlo. Al añadir una mutación nueva, verificar su persistencia con una **petición GET independiente** después (no solo mirar la respuesta de la propia mutación).

## Estado actual

MVP completo: backend con persistencia real en SQLite (Parte 6), consumido por el frontend (Parte 7), conectividad con OpenRouter (Parte 8), integración de la IA con el Kanban vía Structured Outputs (Parte 9) y chat en la interfaz (Parte 10). Todas las partes de `docs/PLAN.md` están implementadas.

## Ejecutar en local sin Docker

```
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

## Tests

```
cd backend
uv sync
uv run pytest
```
