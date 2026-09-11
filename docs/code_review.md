# Revisión de código

Revisión exhaustiva de todo el repositorio (`backend/`, `frontend/`, `scripts/`, raíz), no solo del diff actual. Cada hallazgo se verificó leyendo el código real antes de incluirlo aquí.

## Hallazgos

### 1. Las operaciones de la IA sobre el tablero no son atómicas

- **Archivo:** `backend/app/main.py:210` (bucle en `_apply_ai_operations`, que llama a `board.apply_ai_operation` por cada operación) y `backend/app/board.py` (cada función `add_card`/`update_card`/`delete_card`/`rename_column`/`move_card` hace su propio `connection.commit()`).
- **Escenario de fallo:** el usuario pide a la IA "crea una tarjeta en Backlog y mueve la tarjeta X a Hecho". La IA devuelve `operations=[create_card(...), move_card(cardId="X")]`, pero `X` ya no existe (tablero desactualizado). `create_card` se ejecuta y confirma su transacción; `move_card` lanza `NotFoundError`; la ruta responde `422`. El usuario ve un error, pero la tarjeta ya se creó y quedó persistida — y como el fallo ocurre antes de `chat.append_message` (líneas 216-217), tampoco queda constancia en el historial del chat.
- **Recomendación:** validar todas las operaciones antes de aplicar ninguna, o envolver el lote completo en una única transacción y hacer rollback si alguna falla.

### 2. Una respuesta malformada de la IA provoca un 500 sin gestionar

- **Archivo:** `backend/app/main.py:210` — `AIOperation.model_validate(op)` no está dentro de ningún `try/except`.
- **Escenario de fallo:** el modelo gratuito (`nvidia/nemotron-3.5-lightning:free`) no garantiza al 100% el cumplimiento del `response_format: json_schema strict`. Si devuelve un campo con un tipo inesperado (p. ej. `toIndex` como cadena numérica), `model_validate` lanza `pydantic.ValidationError`, que no está cubierto por el `except (board.NotFoundError, ValueError)` de la línea 213 — el resultado es un `500` sin gestionar, en vez del `502`/`422` que el resto de la ruta ya usa para fallos de la IA (y que el frontend ya sabe mostrar como "No se ha podido contactar con la IA.").
- **Recomendación:** capturar también `pydantic.ValidationError` alrededor de la construcción de `AIOperation` y devolver `422` con el motivo, igual que se hace con las demás operaciones inválidas.

### 3. `cookies.txt` con un `session_id` real está commiteado en el repositorio

- **Archivo:** `cookies.txt` (raíz, rastreado por git — confirmado con `git ls-files`).
- **Descripción:** es un cookie-jar de `curl` (formato Netscape) que quedó de alguna sesión de depuración manual, con un `session_id` real como valor. Las sesiones actuales viven solo en memoria (`backend/app/auth.py`, `_sessions: set[str]`) y se pierden al reiniciar el contenedor, así que hoy no es explotable. Pero es un descuido de higiene: un secreto de sesión no debería quedar en el historial de git, y si en el futuro la sesión pasa a persistirse (parte del roadmap multiusuario ya previsto en `CLAUDE.md`), cualquier commit histórico de este archivo daría una sesión válida a quien tenga acceso al repo.
- **Recomendación:** eliminar `cookies.txt` del repositorio y añadirlo a `.gitignore` (p. ej. `cookies.txt` o `*.txt` de depuración). No se ha borrado en esta revisión porque implica reescribir el estado del árbol de trabajo de un archivo rastreado — a confirmar contigo antes de actuar.

### 4. `backend/pm_backend.egg-info/` no está en `.gitignore`

- **Archivo:** `.gitignore`.
- **Descripción:** es un artefacto de build generado por `uv sync`/setuptools (visible como `??` en `git status`). El `.gitignore` actual solo ignora `backend/.venv`, `backend/*.db`, `backend/data/` y `.env`, pero no este directorio.
- **Recomendación:** añadir `backend/pm_backend.egg-info/` a `.gitignore` para que no aparezca como ruido en `git status` ni se cuele en un `git add -A` futuro.

### 5. `ensure_default_user` hace un `commit()` de escritura en cada petición, incluidas las lecturas

- **Archivo:** `backend/app/board.py:83-89`, invocada desde `require_board` (usado por todas las rutas `/api/board*`) y desde `_load_board_for_ai`.
- **Descripción:** cada petición —incluido un simple `GET /api/board`— ejecuta un `INSERT OR IGNORE` más `connection.commit()` para reafirmar una fila que, tras la primera petición, ya existe siempre.
- **Impacto:** bajo para el volumen del MVP (SQLite local, un único usuario hardcodeado), pero es E/S y una transacción de escritura innecesarias en cada lectura, que además podría serializarse con otra escritura concurrente (p. ej. mientras `/api/ai/chat` mantiene una conexión abierta durante los ~200s de espera a la IA).
- **Recomendación:** separar "asegurar que existe" (una vez, en el arranque o en login) de "leer el id", o cachear el resultado en memoria dado que el usuario es fijo en el MVP.

### 6. Las sesiones y los historiales de chat crecen sin límite si no se hace logout

- **Archivo:** `backend/app/auth.py:11` (`_sessions: set[str]`) y `backend/app/chat.py:3` (`_histories: dict[str, list[ChatMessage]]`).
- **Escenario de fallo:** si el usuario cierra la pestaña sin pulsar "Cerrar sesión" (el caso más habitual) y vuelve a iniciar sesión más tarde, se añade un nuevo `session_id` a `_sessions` sin eliminar el anterior, y `chat._histories` acumula una lista de mensajes por cada sesión que nunca se purga. En un contenedor pensado para ejecutarse de forma continua, esto es un crecimiento de memoria sin límite a lo largo de muchos días de uso.
- **Recomendación:** expirar sesiones inactivas (TTL) o, como mínimo, limitar cuántas sesiones/historiales se conservan en memoria. Baja prioridad para el MVP de un solo usuario, pero a tener en cuenta antes de soportar múltiples usuarios reales.

## Resumen

| # | Hallazgo | Severidad | Estado |
|---|---|---|---|
| 1 | Operaciones de IA no atómicas | Media | Resuelto |
| 2 | `ValidationError` sin capturar → 500 | Media | Resuelto |
| 3 | `cookies.txt` con secreto commiteado | Media (higiene/seguridad) | Resuelto |
| 4 | `egg-info` fuera de `.gitignore` | Baja | Resuelto |
| 5 | `commit()` de escritura en cada lectura | Baja | Resuelto |
| 6 | Sesiones/historiales sin límite | Baja | Resuelto |

## Correcciones aplicadas

1. **Operaciones de IA no atómicas:** nueva `board.validate_ai_operation()` que comprueba campos requeridos y que los ids referenciados existen en el snapshot del tablero **antes** de aplicar ninguna operación del lote (`app/main.py`, `_apply_ai_operations`). Si cualquiera falla, no se aplica ninguna. Test de regresión: `test_ai_chat_endpoint_does_not_partially_apply_an_invalid_batch`.
2. **`ValidationError` sin capturar:** `AIOperation.model_validate(op)` ahora está en su propio `try/except ValidationError`, devolviendo `422` en vez de un `500` sin gestionar. Test de regresión: `test_ai_chat_endpoint_returns_422_on_malformed_ai_operation`.
3. **`cookies.txt`:** eliminado del repositorio (`git rm`) y añadido a `.gitignore`. Sigue existiendo en el historial de git; si se quiere purgar también de ahí (reescribir historia), es una decisión aparte a confirmar explícitamente.
4. **`egg-info` fuera de `.gitignore`:** añadido `backend/pm_backend.egg-info/` a `.gitignore`.
5. **`commit()` en cada lectura:** `ensure_default_user` ahora primero intenta un `SELECT`; solo hace `INSERT` + `commit()` la primera vez que el usuario no existe.
6. **Sesiones/historiales sin límite:** las sesiones ahora guardan su fecha de creación y expiran a las 24h (`SESSION_TTL_SECONDS` en `app/auth.py`), purgándose (junto a su historial de chat) de forma perezosa en cada login y en cada comprobación de sesión. Test de regresión: `test_expired_sessions_are_evicted_and_rejected`.

**Verificación:** suite de backend 48/48 en verde (45 anteriores + 3 tests de regresión nuevos), suite de frontend 22/22, e2e de tablero (Playwright) 6/6 contra el contenedor Docker reconstruido con las correcciones.
