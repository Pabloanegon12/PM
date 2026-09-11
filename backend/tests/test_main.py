from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from app.main import app as real_app


def test_health():
    client = TestClient(real_app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_serves_static_index():
    client = TestClient(real_app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_static_mount_serves_index_and_assets(tmp_path: Path):
    (tmp_path / "index.html").write_text("<html><body>ok</body></html>")
    (tmp_path / "app.js").write_text("console.log('ok');")

    app = FastAPI()
    app.mount("/", StaticFiles(directory=tmp_path, html=True), name="static")
    client = TestClient(app)

    root_response = client.get("/")
    assert root_response.status_code == 200
    assert "text/html" in root_response.headers["content-type"]

    asset_response = client.get("/app.js")
    assert asset_response.status_code == 200
    assert "console.log" in asset_response.text
