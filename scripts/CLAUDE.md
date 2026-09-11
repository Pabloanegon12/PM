# Scripts

Arranque y parada del contenedor Docker de la aplicación (imagen `pm-app`, contenedor `pm-app`, puerto `8000`).

- `start.sh` / `start.ps1`: construyen la imagen (`docker build`) y arrancan el contenedor en segundo plano (`docker run -d --rm`), pasando las variables de `.env` y montando `./data` (raíz del proyecto) en `/app/data` para que la base de datos SQLite persista entre reinicios.
- `stop.sh` / `stop.ps1`: detienen el contenedor (`docker stop`); al llevar `--rm`, se elimina automáticamente al detenerse.

Usar los `.sh` en Mac/Linux y los `.ps1` en Windows (PowerShell). Requieren Docker Desktop/Engine en marcha y un `.env` en la raíz del proyecto con `OPENROUTER_API_KEY`.
