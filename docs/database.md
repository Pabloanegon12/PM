# Base de datos

Esquema propuesto para el Kanban, guardado como JSON en `docs/db-schema.json`.

## Motor

SQLite (ya decidido en `CLAUDE.md`), con claves foráneas activadas (`PRAGMA foreign_keys = ON`) para que los `ON DELETE CASCADE` se respeten.

## Tablas

- **`users`**: preparada para el futuro multiusuario. En el MVP el login sigue con las credenciales hardcodeadas (Parte 4), sin consultar esta tabla; `password_hash` queda `nullable` hasta que se implemente autenticación real contra la base de datos.
- **`boards`**: un tablero por usuario. `UNIQUE(user_id)` fuerza el límite de "1 tablero por usuario" del MVP; en el futuro basta con quitar esa restricción para soportar varios tableros por usuario sin cambiar la estructura.
- **`columns`**: columnas del tablero (nombre editable), con `position` (entero, empezando en 0) para mantener su orden.
- **`cards`**: tarjetas de cada columna, con `position` (entero, empezando en 0 dentro de su columna) para el orden usado por el drag & drop.

## Orden de columnas y tarjetas

En vez de guardar un array de ids (como hace ahora mismo el frontend en memoria), cada fila guarda su propio `position`. Al mover o reordenar, el backend reindexa las posiciones afectadas (0..n-1) de la columna de origen y destino. Es una operación simple sobre pocas filas por columna, coherente con no sobreingenierizar la ordenación (se descarta un esquema de posiciones fraccionarias/gaps por ser innecesario para el volumen de datos de este MVP).

## Relación con el modelo actual del frontend

`frontend/src/lib/types.ts` (`Board { columns, cards }`) se mapea así:
- Cada `Column` del frontend es una fila de `columns` (más su lista de `cards` obtenida por `column_id` y ordenada por `position`).
- Cada `Card` del frontend es una fila de `cards`.

La Parte 6 traducirá esto a los modelos y endpoints reales; la Parte 7 hará que el frontend consuma esa API en vez del estado en memoria (`seedData.ts` + `boardReducer.ts`).

## Creación automática

Al arrancar el backend, si `pm.db` no existe se crea junto con estas tablas (Parte 6). El usuario `user` y su tablero (con las columnas/tarjetas semilla equivalentes a `seedData.ts`) se crean la primera vez que se accede sin tablero existente.
