from fastapi.testclient import TestClient

from app.main import app


def test_login_with_correct_credentials_sets_session_cookie():
    client = TestClient(app)
    response = client.post("/api/login", json={"username": "user", "password": "password"})
    assert response.status_code == 200
    assert "session_id" in response.cookies


def test_login_with_wrong_credentials_is_rejected():
    client = TestClient(app)
    response = client.post("/api/login", json={"username": "user", "password": "wrong"})
    assert response.status_code == 401
    assert "session_id" not in response.cookies


def test_me_without_session_is_unauthorized():
    client = TestClient(app)
    response = client.get("/api/me")
    assert response.status_code == 401


def test_me_with_session_is_authorized():
    client = TestClient(app)
    client.post("/api/login", json={"username": "user", "password": "password"})
    response = client.get("/api/me")
    assert response.status_code == 200


def test_logout_invalidates_session():
    client = TestClient(app)
    client.post("/api/login", json={"username": "user", "password": "password"})
    logout_response = client.post("/api/logout")
    assert logout_response.status_code == 200

    me_response = client.get("/api/me")
    assert me_response.status_code == 401
