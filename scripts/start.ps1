Set-Location "$PSScriptRoot\.."

docker build -t pm-app .
docker run -d --name pm-app --rm -p 8000:8000 --env-file .env -v "${PWD}/data:/app/data" pm-app

Write-Host "PM disponible en http://localhost:8000"
