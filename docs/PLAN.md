# Pasos generales del proyecto

Cada parte incluye una lista de verificación de subpasos, las pruebas a realizar y los criterios de éxito. Se debe completar y validar una parte antes de pasar a la siguiente.

## Parte 1: Planificación

- [x] Ampliar este documento con subpasos, pruebas y criterios de éxito por parte.
- [x] Crear `frontend/CLAUDE.md` describiendo el código existente en `frontend/`.
- [ ] Revisión y aprobación del usuario antes de continuar con la Parte 2.

**Criterio de éxito:** el usuario aprueba explícitamente este plan.

## Parte 2: Estructura inicial

- [x] Crear `backend/` con FastAPI, usando `uv` como gestor de paquetes (`pyproject.toml` + `uv.lock`).
- [x] Añadir un endpoint `GET /api/health` que devuelva un JSON simple (p. ej. `{"status": "ok"}`) para confirmar que la API responde.
- [x] Servir en `/` un HTML estático de ejemplo ("Hello World"), sin el frontend real todavía.
- [x] Crear el `Dockerfile` en la raíz del proyecto que empaquete el backend (imagen Python + `uv`).
- [x] Configurar la lectura de variables de entorno desde `.env` (para `OPENROUTER_API_KEY`, usada más adelante).
- [x] Crear en `scripts/` los scripts de arranque y parada para Mac/Linux (`start.sh`, `stop.sh`) y Windows (`start.ps1`, `stop.ps1`), que construyan y ejecuten/detengan el contenedor Docker.
- [x] Actualizar `backend/CLAUDE.md` y `scripts/CLAUDE.md` con la descripción real de cada carpeta.

**Pruebas:**
- [x] Construir la imagen Docker sin errores.
- [x] Con el contenedor en marcha: `GET /` devuelve el HTML de ejemplo y `GET /api/health` devuelve el JSON esperado.
- [x] Ejecutar el script de arranque y el de parada y comprobar que el contenedor se inicia y se detiene correctamente.

**Criterio de éxito:** la aplicación arranca en Docker mediante los scripts, sirve el "Hello World" y responde en el endpoint de prueba de la API.

## Parte 3: Integrar el frontend

- [x] Configurar `next.config.ts` para generar una build estática (export).
- [x] Actualizar el `Dockerfile` a build multi-stage: una etapa de Node que compila el frontend y una etapa final de Python/`uv` que sirve los estáticos generados junto con la API.
- [x] Montar en FastAPI el directorio estático generado por Next.js para que el tablero Kanban de demo se sirva en `/`.
- [x] Ajustar scripts en `scripts/` si el proceso de build cambia (no ha hecho falta: siguen llamando a `docker build`/`docker run` igual).
- [x] Añadir pruebas de integración en el backend (`backend/tests/test_main.py`, con `TestClient`) que verifiquen que `/` devuelve HTML y que los assets estáticos se sirven correctamente.
- [x] Mantener en verde las pruebas unitarias de frontend ya existentes (`boardReducer.test.ts`, `BoardApp.test.tsx`).

**Pruebas:**
- [x] Pruebas unitarias de frontend (`npm test` en `frontend/`): 16 tests en verde.
- [x] Pruebas de integración de backend sirviendo los estáticos (`uv run pytest`): 3 tests en verde.
- [x] Verificación manual (vía `curl`, contenedor real): `http://localhost:8000/` sirve el tablero Kanban con sus columnas y tarjetas, `/api/health` responde y un asset estático (`favicon.ico`) carga con HTTP 200.

**Criterio de éxito:** el tablero Kanban de demo se ve y funciona (drag & drop, edición local) servido desde el contenedor Docker único, con todas las pruebas en verde.

## Parte 4: Añadir un inicio de sesión de usuario simulado

- [x] Backend: endpoint `POST /api/login` que valide las credenciales hardcodeadas `user` / `password` y establezca una sesión (cookie de sesión simple).
- [x] Backend: endpoint `POST /api/logout` que cierre la sesión.
- [x] Backend: endpoint o dependencia para comprobar si hay sesión activa (`GET /api/me`, dependencia `require_session`), lista para proteger las rutas del Kanban en la Parte 6.
- [x] Frontend: pantalla de login (usuario/contraseña) que se muestra antes del tablero (`LoginForm`).
- [x] Frontend: al cargar la aplicación, comprobar si existe sesión activa; si no, mostrar login; si sí, mostrar el tablero (`AuthGate`).
- [x] Frontend: botón de cerrar sesión visible tras iniciar sesión.

**Pruebas:**
- [x] Backend: tests unitarios de login correcto, login incorrecto, logout, y acceso denegado a `/api/me` sin sesión (`backend/tests/test_auth.py`, 5 tests).
- [x] Frontend: tests de renderizado del formulario de login, envío con credenciales correctas e incorrectas, `AuthGate` (login vs. tablero) y logout (`LoginForm.test.tsx`, `AuthGate.test.tsx`, test añadido a `BoardApp.test.tsx`).
- [x] Prueba end-to-end manual contra el contenedor real (`curl`): `/api/me` sin sesión → 401, login incorrecto → 401, login correcto → 200 + cookie, `/api/me` con sesión → 200, logout → 200, `/api/me` tras logout → 401.

**Criterio de éxito:** no es posible ver el tablero sin iniciar sesión con `user`/`password`, y el logout funciona correctamente.

## Parte 5: Modelado de la base de datos

- [x] Proponer el esquema de la base de datos (tablas `users`, `boards`, `columns`, `cards`, con el orden de columnas/tarjetas), preparado para múltiples usuarios y múltiples tableros en el futuro aunque el MVP solo use uno de cada.
- [x] Guardar el esquema propuesto como JSON en `docs/` (`docs/db-schema.json`).
- [x] Documentar en `docs/` el razonamiento detrás de las decisiones de modelado (`docs/database.md`).
- [x] Presentar el esquema al usuario y esperar su aprobación antes de la Parte 6 (aprobado).

**Criterio de éxito:** el usuario aprueba explícitamente el esquema de base de datos.

## Parte 6: Backend

- [x] Configurar SQLite con creación automática de la base de datos y las tablas si no existen al arrancar la aplicación (`app/db.py`, `init_db` en el `lifespan` de la app).
- [x] Modelos Pydantic para `Board`, `Column` y `Card` (`app/schemas.py`).
- [x] Rutas de API para leer el tablero del usuario autenticado y para crear/editar/eliminar tarjetas, renombrar columnas y mover tarjetas entre columnas (`app/main.py`, lógica en `app/board.py`).
- [x] Proteger todas estas rutas con la sesión de la Parte 4 (`require_board`, que combina `require_session` + resolución del tablero).
- [x] Sembrar datos iniciales al crear el tablero de un usuario por primera vez (mismas 5 columnas / 9 tarjetas que `seedData.ts`).
- [x] Persistencia de la base de datos entre reinicios del contenedor: volumen `./data:/app/data` añadido a `scripts/start.sh` y `scripts/start.ps1`.

**Pruebas:**
- [x] Tests unitarios de backend (pytest) para cada ruta: casos correctos y casos de error (tarjeta/columna inexistente, sin sesión, nombre/título vacío) — `backend/tests/test_board.py`, 18 tests.
- [x] Test que arranca con una base de datos inexistente y comprueba que se crea automáticamente con el esquema correcto (tablas `users`, `boards`, `columns`, `cards`).
- [x] Suite completa de backend: 25 tests en verde (`uv run pytest`).
- [x] Verificación manual en Docker real: login, `GET /api/board` (semilla correcta), crear tarjeta, reiniciar el contenedor y comprobar que la tarjeta creada sigue ahí (persistencia via volumen).

**Criterio de éxito:** cobertura de pruebas exhaustiva en verde sobre todas las rutas del Kanban; la base de datos se autogenera en un entorno limpio.

## Parte 7: Frontend + Backend

- [x] Sustituir el estado local (`seedData` + reducer en memoria) por llamadas reales a la API: cargar el tablero al iniciar (`GET /api/board`) y sincronizar cada acción (crear, borrar, renombrar, mover) con el backend.
- [x] Manejo simple de estados de carga y error (mensaje de "Cargando tablero…" y un aviso de error inline, sin reintentos ni librerías extra).
- [x] Actualizar las pruebas de frontend para mockear la API (`vi.mock("@/lib/api")` en `BoardApp.test.tsx`).
- [x] Añadir pruebas end-to-end (Playwright) que verifiquen que los cambios persisten tras recargar la página (`e2e/board.spec.ts`, contra el contenedor Docker real).

**Pruebas:**
- [x] Pruebas unitarias/de integración de frontend con la API mockeada: 17 tests en verde (`npm test`).
- [x] Pruebas end-to-end contra el backend real (contenedor Docker) verificando persistencia tras recargar: 5 tests en verde (`npm run test:e2e`) — login requerido, crear tarjeta, borrar tarjeta, renombrar columna y arrastrar tarjeta entre columnas, todas comprobando que el cambio sigue ahí tras `page.reload()`.
- [x] Bug real encontrado y corregido gracias a los tests e2e: al arrastrar una tarjeta entre columnas, el punto donde se soltaba el ratón podía coincidir con la propia tarjeta ya reubicada por la vista previa optimista, así que `handleDragEnd` cancelaba la llamada a la API (`activeId === overId`) y el movimiento nunca se persistía, aunque visualmente parecía correcto hasta recargar la página. Corregido en `BoardApp.tsx` para que siempre persista la posición final de la tarjeta tal y como quedó localmente.

**Criterio de éxito:** el tablero Kanban es completamente persistente a través del backend; recargar la página no pierde cambios.

## Parte 8: Conectividad con IA

- [x] Backend: cliente HTTP hacia OpenRouter usando `OPENROUTER_API_KEY` desde el entorno y el modelo `nvidia/nemotron-3.5-lightning:free` (`app/ai.py`, `httpx2`).
- [x] Endpoint de prueba `POST /api/ai/test` que envía una pregunta fija ("¿Cuánto es 2+2?") y devuelve la respuesta de la IA.
- [x] Manejo básico de errores (clave inválida/ausente, fallo HTTP o de red) mediante una única excepción `AIError`, mapeada a HTTP 502 en la ruta.

**Pruebas:**
- [x] Tests unitarios del cliente OpenRouter con la llamada HTTP mockeada (`backend/tests/test_ai.py`): respuesta correcta, sin clave, error HTTP, error de red.
- [x] Tests de la ruta `/api/ai/test`: requiere sesión (401), devuelve la respuesta (200), devuelve 502 si la IA falla.
- [x] Suite completa de backend: 32 tests en verde (`uv run pytest`).
- [x] Verificación real contra OpenRouter (contenedor Docker, con la `OPENROUTER_API_KEY` real de `.env`): `POST /api/ai/test` devolvió `{"answer":"4"}` con HTTP 200.

**Criterio de éxito:** la prueba de conectividad 2+2 funciona contra la IA real de OpenRouter.

## Parte 9: Integración de la IA con el Kanban

- [x] Definir el esquema de **Structured Output** de la IA: `{"message": str, "operations": [...]}`, donde `operations` es una lista (vacía si no hace falta cambiar nada) de operaciones `create_card` / `update_card` / `delete_card` / `rename_column` / `move_card` — cada una reutiliza directamente la función correspondiente ya probada en `app/board.py` (Parte 6).
- [x] Endpoint `POST /api/ai/chat`: recibe el mensaje del usuario, envía a la IA el JSON completo del tablero actual, la pregunta y el historial de la conversación de la sesión, y solicita la respuesta en el formato estructurado definido (`response_format: json_schema`, modo `strict`).
- [x] Si la IA devuelve una actualización del tablero, validarla (Pydantic + comprobación de campos requeridos por tipo de operación) y aplicarla a la base de datos; si alguna operación es inválida, se rechaza con 422 y el motivo exacto (p. ej. "Tarjeta no encontrada").
- [x] Persistir el historial de conversación de forma simple: en memoria, por sesión (`app/chat.py`), igual que las sesiones de login; se limpia al hacer logout.

**Pruebas:**
- [x] Tests unitarios con la respuesta de la IA mockeada: solo texto, texto + actualización válida del tablero, y actualización inválida (debe rechazarse identificando la causa) — `backend/tests/test_ai.py`.
- [x] Test que confirma que el tablero en base de datos cambia según lo esperado tras una actualización válida de la IA (`test_ai_chat_endpoint_applies_valid_operation_and_persists`, verificado con un `GET /api/board` posterior).
- [x] Suite completa de backend: 42 tests en verde (`uv run pytest`).
- [x] Verificación real contra OpenRouter (contenedor Docker): pedí por chat crear una tarjeta ("Probar IA") → se creó y persistió (confirmado con `GET /api/board`); pregunta de seguimiento usando el historial ("¿qué tarjeta acabas de crear?") → la IA respondió correctamente "Probar IA", confirmando que el historial de conversación por sesión funciona.
- [x] **Bug real encontrado y corregido**: `httpx2.post()` (síncrono) se cuelga indefinidamente al ejecutarse en un hilo de threadpool mientras hay un *event loop* de asyncio activo (el caso de cualquier ruta FastAPI). Lo reproduje de forma aislada (fuera de FastAPI) para confirmar la causa raíz antes de corregir. Solución: `app/ai.py` usa `httpx2.AsyncClient` con rutas `async def`; y como una conexión SQLite creada por una dependencia síncrona no puede compartirse con una ruta `async def` que además espera a la IA en medio (hilos distintos), `POST /api/ai/chat` abre sus propias conexiones de corta vida en `run_in_threadpool` en vez de usar `Depends(require_board)`. Detalle completo en `backend/CLAUDE.md`.

**Criterio de éxito:** la IA puede crear, editar y mover tarjetas a través del endpoint, y los cambios quedan reflejados correctamente en la base de datos.

## Parte 10: Chat de IA en la interfaz

- [x] Añadir un widget de chat en una barra lateral (siguiendo el esquema de colores del proyecto) conectado a `POST /api/ai/chat` (`ChatSidebar.tsx`).
- [x] Mostrar el historial de la conversación y un indicador de "IA escribiendo" mientras se espera respuesta.
- [x] Cuando la respuesta incluya una actualización del tablero, refrescar automáticamente el tablero en la interfaz (`onBoardUpdate` siempre reemplaza el tablero con la respuesta, se haya modificado o no — más simple que detectar si hubo cambios).

**Pruebas:**
- [x] Tests de frontend con la API mockeada: envío de mensaje, renderizado de la respuesta, refresco del tablero, mensaje vacío no se envía, error de red se muestra (`ChatSidebar.test.tsx`, 20 tests en verde en toda la suite de frontend).
- [x] Prueba end-to-end (Playwright) del flujo completo contra la IA real (no mockeada): escribir en el chat pidiendo crear una tarjeta y ver el tablero actualizarse (`e2e/chat.spec.ts`).
- [x] **Bug real encontrado y corregido gracias a esta prueba e2e**: `move_card` (en `app/board.py`) había perdido su `connection.commit()` al añadir `apply_ai_operation` en la Parte 9 — la respuesta de la propia petición de mover una tarjeta parecía correcta (se genera con la misma conexión/transacción que acaba de escribir, sin confirmar), pero el cambio nunca se guardaba de verdad: al recargar la página, o al hacer una petición GET independiente, la tarjeta volvía a su columna original. Ni los tests de la Parte 6 (que solo comprobaban la respuesta inmediata del propio `move`) ni las verificaciones manuales anteriores lo habían detectado. Se reprodujo primero con curl puro (sin frontend) para confirmar la causa antes de corregirla, se añadió un test de regresión que verifica persistencia con una petición GET independiente, y se corrigió también una prueba e2e de drag & drop que fallaba por la misma causa.

**Criterio de éxito:** el usuario puede conversar con la IA desde la barra lateral y ve el tablero actualizarse automáticamente cuando la IA lo modifica.

## Post-Parte 10: edición de tarjetas en la interfaz y revisión conjunta

El usuario detectó, al revisar todo en conjunto, que faltaba una forma de editar el título/detalles de una tarjeta ya creada desde la interfaz (el backend ya lo soportaba desde la Parte 6 vía `PATCH /api/board/cards/{id}`, pero no había ningún botón para ello). Se añadió:

- [x] Botón "✎ Editar" junto al de eliminar en cada tarjeta (visible al pasar el ratón), que abre un formulario in-place con título y detalles (`CardItem.tsx`).
- [x] Tests de frontend (guardar edición, cancelar sin llamar a la API) y test e2e con recarga de página.
- [x] **Bug real encontrado y corregido**: al hacer clic en los nuevos botones de editar/eliminar, `userEvent` (y potencialmente un usuario real navegando por teclado) dispara también eventos de teclado de activación accesible (Espacio/Enter) que burbujean hasta el envoltorio arrastrable de la tarjeta; el `KeyboardSensor` de dnd-kit los interpretaba como "iniciar arrastre por teclado", duplicando la tarjeta en pantalla (una normal + una en estado `isDragging`/`DragOverlay`). Cortar solo `onPointerDown` (como ya hacía el botón de eliminar) no bastaba; hubo que cortar también `onKeyDown`.
- [x] Verificación conjunta de todas las Partes 1-10 tras corregir estos bugs: 44 tests de backend, 22 de frontend y 7 e2e de Playwright (incluyendo el chat real con la IA) en verde; persistencia de las 5 mutaciones (crear, editar, borrar, renombrar, mover) confirmada con peticiones GET independientes y tras reiniciar el contenedor completo.

Ver `frontend/CLAUDE.md` y `backend/CLAUDE.md` para el detalle técnico de ambos bugs.
