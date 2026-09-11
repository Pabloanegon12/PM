# La aplicación web MVP de Gestión de Proyectos

## Requisitos de negocio

Este proyecto consiste en desarrollar una aplicación de Gestión de Proyectos. Características principales:

- Un usuario puede iniciar sesión.
- Una vez iniciada la sesión, el usuario ve un tablero Kanban que representa su proyecto.
- El tablero Kanban tiene columnas fijas que pueden cambiarse de nombre.
- Las tarjetas del tablero Kanban pueden moverse mediante arrastrar y soltar (drag and drop), y también pueden editarse.
- Hay una función de chat con IA en una barra lateral; la IA puede crear, editar y mover una o varias tarjetas.

## Limitaciones

Para el MVP, solo habrá un inicio de sesión de usuario (con las credenciales hardcodeadas `user` y `password`), pero la base de datos estará preparada para soportar múltiples usuarios en el futuro.

Para el MVP, solo habrá 1 tablero Kanban por cada usuario que haya iniciado sesión.

Para el MVP, la aplicación se ejecutará localmente (dentro de un contenedor Docker).

## Decisiones técnicas

- Frontend con Next.js.
- Backend con Python FastAPI, incluyendo el servicio del Next.js estático en `/`.
- Todo estará empaquetado dentro de un contenedor Docker.
- Usar `uv` como gestor de paquetes de Python dentro del contenedor Docker.
- Usar OpenRouter para las llamadas a la IA. La variable `OPENROUTER_API_KEY` se encuentra en el archivo `.env` en la raíz del proyecto.
- Usar `nvidia/nemotron-3.5-lightning:free` como modelo.
- Usar una base de datos local SQLite, creando una nueva base de datos si no existe.
- Incluir scripts para iniciar y detener el servidor en Mac, PC y Linux dentro de `scripts/`.

## Punto de partida

Ya se ha desarrollado un MVP funcional del frontend y se encuentra en `frontend/`. Todavía no está preparado para la configuración con Docker.

Es una demo exclusivamente de frontend.

**Nota:** este era el punto de partida original. El MVP completo (backend, base de datos, Docker, IA) ya está implementado; ver "Estado actual" más abajo y `docs/PLAN.md` para el detalle de cada parte.

## Estado actual

Las 10 partes de `docs/PLAN.md` están completas: login, tablero Kanban persistente en SQLite, chat de IA (OpenRouter) capaz de crear/editar/mover tarjetas, todo empaquetado en un único contenedor Docker (Next.js exportado como estático + FastAPI). Para el detalle de arquitectura de cada parte, ver el `CLAUDE.md` de cada directorio: [`backend/CLAUDE.md`](backend/CLAUDE.md), [`frontend/CLAUDE.md`](frontend/CLAUDE.md), [`scripts/CLAUDE.md`](scripts/CLAUDE.md).

## Comandos

**Arrancar/parar la app completa (Docker):**
```
scripts/start.sh   # o scripts/start.ps1 en Windows
scripts/stop.sh    # o scripts/stop.ps1 en Windows
```
Requiere Docker en marcha y `.env` en la raíz con `OPENROUTER_API_KEY`. Sirve en `http://localhost:8000`.

**Backend (FastAPI) en local, sin Docker:**
```
cd backend
uv sync
uv run uvicorn app.main:app --reload
```
Tests: `cd backend && uv run pytest` (un solo test: `uv run pytest tests/test_board.py::nombre_del_test`).

**Frontend (Next.js) en local, sin Docker:**
```
cd frontend
npm install
npm run dev
```
Tests unitarios: `npm test` (un solo archivo: `npm test -- src/components/BoardApp.test.tsx`). Lint: `npm run lint`.
Tests e2e (Playwright, requieren el contenedor Docker real en `localhost:8000`): `npm run test:e2e`.

## Arquitectura

Contenedor único: `Dockerfile` en la raíz hace build multi-stage — Node compila el frontend (`next build`, export estático) y una imagen Python/`uv` sirve ese estático junto con la API FastAPI, ambos en el puerto 8000. El backend monta el build del frontend en `/`; todas las rutas de API van bajo `/api/*`. La base de datos SQLite vive en `./data/pm.db` (montada como volumen para persistir entre reinicios del contenedor). Para la estructura interna de cada mitad (rutas, componentes, dónde vive cada cosa) ver `backend/CLAUDE.md` y `frontend/CLAUDE.md`.

## Esquema de colores

- **Amarillo de acento:** `#ecad0a` — líneas de acento y elementos destacados.
- **Azul primario:** `#209dd7` — enlaces y secciones principales.
- **Morado secundario:** `#753991` — botones de envío y acciones importantes.
- **Azul marino oscuro:** `#032147` — encabezados principales.
- **Texto gris:** `#888888` — textos secundarios y etiquetas.

## Estándares de código

1. Utilizar las versiones más recientes de las librerías y enfoques idiomáticos vigentes a día de hoy.
2. Mantenerlo simple: **NUNCA** sobreingenierizar, **SIEMPRE** simplificar y **NO** añadir programación defensiva innecesaria. No añadir funcionalidades extra; centrarse en la simplicidad.
3. Ser conciso. Mantener el `README` al mínimo. **IMPORTANTE:** no utilizar emojis nunca.
4. Cuando surjan problemas, identificar siempre la causa raíz antes de intentar solucionarlos. No hacer suposiciones. Demostrar la causa con evidencias y, después, corregir la causa raíz.

## Documentación de trabajo

Todos los documentos para la planificación y ejecución de este proyecto estarán en el directorio `docs/`.

Por favor, revisa el documento `docs/PLAN.md` antes de continuar.