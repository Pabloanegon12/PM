# Frontend

MVP completo: login, tablero Kanban persistente y chat de IA en barra lateral, todo consumiendo la API real del backend.

## Stack

- Next.js 16 (App Router) + React 19 + TypeScript.
- Tailwind CSS 4 para estilos, con los tokens de color del proyecto definidos en `src/app/globals.css` (`@theme inline`): `accent-yellow`, `primary-blue`, `secondary-purple` / `secondary-purple-dark`, `navy`, `muted-gray`.
- `@dnd-kit/core` + `@dnd-kit/sortable` para el arrastrar y soltar de tarjetas.
- Vitest + Testing Library para pruebas unitarias/de componentes (`npm test`).
- Playwright para e2e (`npm run test:e2e`) contra el contenedor Docker real (ver más abajo).

## Estructura

- `src/app/layout.tsx`, `src/app/page.tsx`, `src/app/globals.css`: entrada de App Router. `page.tsx` renderiza `AuthGate`.
- `src/components/AuthGate.tsx`: comprueba `GET /api/me` al montar; muestra `LoginForm` o `BoardApp` según haya sesión.
- `src/components/LoginForm.tsx`: formulario de login (`POST /api/login`).
- `src/components/BoardApp.tsx`: componente raíz del tablero. Carga el tablero con `GET /api/board` al montar, gestiona el `DndContext` y llama a la API tras cada acción (crear/editar/eliminar tarjeta, renombrar columna, mover tarjeta), reemplazando el estado local por la respuesta del servidor. Durante el arrastre usa `moveCardInBoard` solo para la vista previa optimista entre columnas; el commit real ocurre en `onDragEnd`. Renderiza el tablero y `ChatSidebar` uno al lado del otro.
- `src/components/ChatSidebar.tsx`: barra lateral de chat con la IA (`POST /api/ai/chat`). Mantiene su propio historial de mensajes en estado local, muestra "IA escribiendo…" mientras espera respuesta, y llama a `onBoardUpdate(board)` con el tablero devuelto tras cada respuesta (la IA puede haberlo modificado o no; refrescar siempre es más simple que intentar detectar si hubo cambios).
- `src/components/Board.tsx`: renderiza las columnas; recibe `onAddCard`/`onEditCard`/`onDeleteCard`/`onRenameColumn` y los pasa a cada `Column`.
- `src/components/Column.tsx`: columna droppable; renombrar in-place y añadir tarjetas, delegando en los callbacks recibidos.
- `src/components/SortableCard.tsx`: envoltorio draggable/sortable de una tarjeta.
- `src/components/CardItem.tsx`: presentación de una tarjeta, con edición in-place (botones "✎" editar / "×" eliminar que aparecen al pasar el ratón). El formulario de edición y los botones cortan la propagación de `onPointerDown` **y** `onKeyDown` — si no se corta `onKeyDown`, un clic simulado (o la activación por teclado de un botón enfocado con Espacio/Enter) burbujea hasta el envoltorio arrastrable de `SortableCard` y el `KeyboardSensor` de dnd-kit lo interpreta como "iniciar arrastre por teclado", duplicando la tarjeta (una copia normal + una en `isDragging`/`DragOverlay`). Bug real encontrado con un test que fallaba con "Found multiple elements with the text..." — cualquier botón nuevo dentro de una tarjeta debe cortar ambos eventos, no solo `onPointerDown`.
- `src/components/AddCardForm.tsx`: formulario inline para crear una tarjeta.
- `src/lib/types.ts`: tipos `Card`, `Column`, `Board` (coinciden con el JSON que devuelve la API).
- `src/lib/api.ts`: cliente fino sobre `fetch` para `/api/board*` y `/api/ai/chat` (`fetchBoard`, `createCard`, `updateCard`, `deleteCard`, `renameColumn`, `moveCard`, `chatWithAI`); todas las peticiones usan `credentials: "include"`.
- `src/lib/boardDrag.ts`: `moveCardInBoard`, único helper puro que queda del antiguo reducer — solo para la reubicación visual optimista durante el arrastre.
- `src/lib/seedData.ts`: ya no inicializa el estado de la app (eso lo hace la API); se mantiene como dato de referencia para tests.

## Estado actual

MVP completo según `CLAUDE.md`: login, tablero Kanban persistente con drag & drop, crear/editar/eliminar tarjetas, renombrar columnas, y chat de IA que puede hacer lo mismo (Partes 1-10 de `docs/PLAN.md` completas, más edición de tarjetas en la UI añadida a petición del usuario tras la Parte 10).

## Pruebas e2e (Playwright)

`playwright.config.ts` apunta a `http://localhost:8000` (el contenedor Docker) y no arranca ningún servidor por sí mismo — hay que levantarlo antes con `scripts/start.sh` / `scripts/start.ps1`. Viewport ampliado a 2000×1000 para que quepan las 5 columnas del tablero más la barra lateral de chat sin necesitar scroll horizontal (un scroll a mitad de una prueba de drag & drop invalida las coordenadas de ratón ya capturadas). Como el MVP solo tiene un tablero compartido (sin aislamiento por test), los tests están forzados a ejecutarse en serie (`workers: 1`, `fullyParallel: false`); cada test crea sus propios datos con títulos únicos y limpia lo que crea (o revierte el nombre de columna que cambia).

`e2e/chat.spec.ts` habla con la IA real (no mockeada) — el modelo `nvidia/nemotron-3.5-lightning:free` es un modelo "razonador" y puede tardar 30-90s (a veces más) en responder, así que ese test usa timeouts mucho más altos (~200s) que el resto de la suite.
