#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker build -t pm-app .
docker run -d --name pm-app --rm -p 8000:8000 --env-file .env -v "$(pwd)/data:/app/data" pm-app

echo "PM disponible en http://localhost:8000"
