# Backend

FastAPI + `uv`, empaquetado en el `Dockerfile` de la raíz del proyecto.

## Estructura

- `pyproject.toml`: dependencias gestionadas con `uv` (`fastapi`, `uvicorn`, `httpx2`; grupo `dev` con `pytest`).
- `app/main.py`: solo crea la app FastAPI, ejecuta `init_db()` en el `lifespan`, registra los routers de `app/routers/` y monta `app/static/` en `/` (sirve el build del frontend). No contiene lógica de rutas — eso vive en `app/routers/` (ver más abajo); se separó de un único `main.py` monolítico para que cada dominio (salud, sesión, tablero, IA) sea un módulo independiente.
- `app/routers/health.py`, `app/routers/auth.py`, `app/routers/board.py`, `app/routers/ai.py`: un `APIRouter` por dominio, con las rutas HTTP y su lógica de request/response. `app/routers/board.py` define `require_board` (combina `Depends(get_db)` + `Depends(require_session)` + resolución del tablero) igual que antes. `app/routers/ai.py` contiene `_load_board_for_ai`/`_apply_ai_operations` (ver la nota sobre `httpx2` más abajo). Estos módulos comparten nombre con los módulos de dominio de nivel superior (`app/auth.py`, `app/board.py`, `app/ai.py`) pero son paquetes distintos: los de `app/routers/` son las rutas HTTP, los de nivel superior son la lógica de negocio/acceso a datos que consumen.
- `app/static/`: estático servido en `/`. En local (sin Docker) contiene el placeholder de la Parte 2; en la imagen Docker se sustituye por el build real del frontend (Parte 3).
- `app/auth.py`: sesión en memoria mediante cookie `httponly` (`session_id`) y credenciales hardcodeadas (`user`/`password`). Expone `require_session` como dependencia para proteger rutas. Cada sesión guarda su fecha de creación y expira a las 24h (`SESSION_TTL_SECONDS`); la purga de sesiones (y su historial de chat asociado) es perezosa, ocurre en cada login y en cada comprobación de sesión.
- `app/db.py`: conexión SQLite (stdlib `sqlite3`, sin ORM) y creación automática del esquema (`init_db`, ejecutado en el `lifespan` de la app). Ruta configurable con la variable de entorno `PM_DB_PATH` (por defecto `backend/data/pm.db`, útil para aislar tests).
- `app/schemas.py`: modelos Pydantic de entrada/salida de la API (`Board`, `Column`, `Card`, `LoginRequest` y los payloads de cada mutación), con nombres de campo en camelCase para que coincidan con el contrato que ya usa el frontend.
- `app/board.py`: capa de acceso a datos del tablero (siembra inicial, lectura y mutaciones — crear/editar/eliminar tarjeta, renombrar columna, mover tarjeta). El orden de columnas y tarjetas se guarda como un entero `position` por fila; mover una tarjeta reindexa las columnas de origen y destino. `ensure_default_user` primero intenta un `SELECT`, solo hace `INSERT`+`commit()` la primera vez que el usuario no existe (evita una escritura innecesaria en cada lectura). `validate_ai_operation(board, operation)` comprueba campos requeridos y que los ids referenciados existen en un snapshot del tablero, sin tocar la base de datos — se usa para validar un lote completo de operaciones de la IA antes de aplicar ninguna (ver más abajo).
- `app/ai.py`: cliente HTTP hacia OpenRouter (`httpx2.AsyncClient`, asíncrono — ver nota sobre `httpx2` más abajo) con el modelo `nvidia/nemotron-3.5-lightning:free`. `ask(prompt)` es la llamada simple de prueba; `chat(board, history, user_message)` construye el prompt de sistema con el tablero completo en JSON y el historial, y pide **Structured Outputs** (`response_format: json_schema`, modo `strict`) con forma `{"message": str, "operations": [...]}`. Lanza `AIError` si falta la clave, si la llamada HTTP falla, si el timeout total se agota, o si la IA no devuelve JSON válido.
- `app/chat.py`: historial de conversación en memoria, indexado por `session_id` (mismo patrón que las sesiones de `app/auth.py`); se limpia al hacer logout o al expirar la sesión.

## Rutas de la API

- `GET /api/health`
- `POST /api/login`, `POST /api/logout`, `GET /api/me`
- `GET /api/board` — devuelve el tablero del usuario autenticado (lo crea con datos semilla la primera vez).
- `POST /api/board/cards`, `PATCH /api/board/cards/{id}`, `DELETE /api/board/cards/{id}`
- `PATCH /api/board/columns/{id}`
- `POST /api/board/cards/{id}/move`
- `POST /api/ai/test` — envía una pregunta fija ("¿Cuánto es 2+2?") a OpenRouter y devuelve `{"answer": "..."}"`; 502 si falla la llamada a la IA.
- `POST /api/ai/chat` — recibe `{"message": "..."}"`, llama a la IA con el tablero completo + historial de la sesión, valida **todo** el lote de operaciones que proponga contra el snapshot del tablero (`board.validate_ai_operation`) y solo si todas son válidas las aplica (`create_card`, `update_card`, `delete_card`, `rename_column`, `move_card`, reutilizando las funciones de `app/board.py`); devuelve `{"message": "...", "board": {...}}` con el tablero ya actualizado. 401 sin sesión, 502 si falla la IA (incluido timeout), 422 si la IA devuelve una operación con forma inválida (no pasa la validación de Pydantic) o si alguna operación del lote es inválida (columna/tarjeta inexistente, faltan campos requeridos) — en ese caso **no se aplica ninguna** operación del lote, no solo las posteriores a la inválida.

Todas las rutas de `/api/board*` y `/api/ai/*` requieren sesión activa (401 si no la hay) y las de `/api/board*` (y `/api/ai/chat`) devuelven el tablero completo actualizado tras cada mutación.

### Nota sobre `httpx2` y rutas asíncronas

`httpx2.post()` (la función síncrona de conveniencia) se cuelga indefinidamente si se ejecuta en un hilo de threadpool mientras hay un *event loop* de asyncio corriendo en el proceso — exactamente la situación de cualquier ruta FastAPI, aunque sea `def` síncrona (FastAPI la ejecuta en un threadpool con el loop de uvicorn activo en el hilo principal). Por eso `app/ai.py` usa `httpx2.AsyncClient` con `await` y las rutas `/api/ai/*` son `async def`. Como consecuencia, `POST /api/ai/chat` no puede depender de la conexión SQLite compartida vía `Depends(require_board)` (esa conexión se crearía en un hilo distinto al que ejecuta el resto de la ruta async, y sqlite3 prohíbe usar una conexión fuera de su hilo de creación): en su lugar abre su propia conexión de corta vida dentro de cada `run_in_threadpool` (ver `_load_board_for_ai` / `_apply_ai_operations` en `app/routers/ai.py`). Las demás rutas (`/api/board*`), al ser totalmente síncronas, no tienen este problema y siguen usando `Depends(require_board)` con normalidad.

**Bug real relacionado, encontrado tras la Parte 10:** el parámetro `timeout` de `httpx2.AsyncClient` solo acota el hueco entre lecturas individuales, no la duración total de la petición. Si la respuesta llega en bytes intermitentes (como hace OpenRouter mientras un modelo razonador "piensa"), cada lectura resetea el timeout y la petición puede colgarse indefinidamente sin que nunca se dispare un error — lo reproduje de forma aislada (`asyncio.wait_for` nunca se disparaba pese a `timeout=120`, y una petición real quedó colgada más de 15 minutos sin que el contenedor la resolviera ni con éxito ni con error). Solución en `app/ai.py`: envolver la llamada `client.post(...)` en `asyncio.wait_for(..., timeout=timeout)`, que sí impone un límite real de duración total. El límite actual de `chat()` es 200s.

### Cada mutación debe confirmar su propia transacción (`connection.commit()`)

`add_card`, `update_card`, `delete_card`, `rename_column` y `move_card` (en `app/board.py`) abren y confirman su propia transacción cada una. Esto importa porque el JSON que devuelve cada ruta se genera con `fetch_board` sobre la **misma conexión** que acaba de escribir, así que refleja el cambio aunque no se haya confirmado todavía — un `commit()` que falte no se nota en la respuesta de esa misma petición, solo se hace evidente al leer con una conexión nueva (la siguiente petición HTTP). Esto pasó de verdad: al añadir `apply_ai_operation` en la Parte 9 se perdió el `connection.commit()` de `move_card`, y ni los tests (que solo comprobaban la respuesta inmediata del propio `move`) ni las pruebas manuales puntuales lo detectaron — hizo falta una prueba e2e con recarga de página (Parte 10) para verlo. Al añadir una mutación nueva, verificar su persistencia con una **petición GET independiente** después (no solo mirar la respuesta de la propia mutación).

## Estado actual

MVP completo: backend con persistencia real en SQLite (Parte 6), consumido por el frontend (Parte 7), conectividad con OpenRouter (Parte 8), integración de la IA con el Kanban vía Structured Outputs (Parte 9) y chat en la interfaz (Parte 10). Todas las partes de `docs/PLAN.md` están implementadas. Ver `docs/code_review.md` para los hallazgos de la revisión de código posterior (todos resueltos) y este mismo documento para el bug del timeout de `httpx2` y el refactor de `app/main.py` a `app/routers/`.

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
