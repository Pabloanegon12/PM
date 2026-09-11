import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import board, db
from app.main import app
from app.schemas import AIOperation


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "test.db"))
    with TestClient(app) as test_client:
        test_client.post("/api/login", json={"username": "user", "password": "password"})
        yield test_client


def test_get_board_returns_seed_data(client: TestClient):
    response = client.get("/api/board")
    assert response.status_code == 200
    board = response.json()
    assert [column["name"] for column in board["columns"]] == [
        "Backlog",
        "Por hacer",
        "En curso",
        "En revisión",
        "Hecho",
    ]
    assert len(board["cards"]) == 9


def test_board_requires_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "anon.db"))
    with TestClient(app) as anon_client:
        response = anon_client.get("/api/board")
    assert response.status_code == 401


def test_create_card(client: TestClient):
    board = client.get("/api/board").json()
    column_id = board["columns"][0]["id"]

    response = client.post(
        "/api/board/cards", json={"columnId": column_id, "title": "Nueva", "details": "Detalle"}
    )
    assert response.status_code == 200
    updated = response.json()
    new_card_id = updated["columns"][0]["cardIds"][-1]
    assert updated["cards"][new_card_id] == {"id": new_card_id, "title": "Nueva", "details": "Detalle"}


def test_create_card_rejects_empty_title(client: TestClient):
    board = client.get("/api/board").json()
    column_id = board["columns"][0]["id"]

    response = client.post("/api/board/cards", json={"columnId": column_id, "title": "  ", "details": ""})
    assert response.status_code == 422


def test_create_card_in_missing_column_returns_404(client: TestClient):
    response = client.post("/api/board/cards", json={"columnId": "9999", "title": "x", "details": ""})
    assert response.status_code == 404


def test_edit_card(client: TestClient):
    board = client.get("/api/board").json()
    card_id = board["columns"][0]["cardIds"][0]

    response = client.patch(f"/api/board/cards/{card_id}", json={"title": "Editado", "details": "Nuevo"})
    assert response.status_code == 200
    assert response.json()["cards"][card_id] == {"id": card_id, "title": "Editado", "details": "Nuevo"}


def test_edit_missing_card_returns_404(client: TestClient):
    response = client.patch("/api/board/cards/9999", json={"title": "x", "details": ""})
    assert response.status_code == 404


def test_delete_card(client: TestClient):
    board = client.get("/api/board").json()
    card_id = board["columns"][0]["cardIds"][0]

    response = client.delete(f"/api/board/cards/{card_id}")
    assert response.status_code == 200
    updated = response.json()
    assert card_id not in updated["cards"]
    assert card_id not in updated["columns"][0]["cardIds"]


def test_delete_missing_card_returns_404(client: TestClient):
    response = client.delete("/api/board/cards/9999")
    assert response.status_code == 404


def test_rename_column(client: TestClient):
    board = client.get("/api/board").json()
    column_id = board["columns"][0]["id"]

    response = client.patch(f"/api/board/columns/{column_id}", json={"name": "Ideas"})
    assert response.status_code == 200
    assert response.json()["columns"][0]["name"] == "Ideas"


def test_rename_column_rejects_empty_name(client: TestClient):
    board = client.get("/api/board").json()
    column_id = board["columns"][0]["id"]

    response = client.patch(f"/api/board/columns/{column_id}", json={"name": "   "})
    assert response.status_code == 422


def test_rename_missing_column_returns_404(client: TestClient):
    response = client.patch("/api/board/columns/9999", json={"name": "Ideas"})
    assert response.status_code == 404


def test_move_card_within_column(client: TestClient):
    board = client.get("/api/board").json()
    column_id = board["columns"][0]["id"]
    first_card_id, second_card_id = board["columns"][0]["cardIds"][:2]

    response = client.post(
        f"/api/board/cards/{first_card_id}/move", json={"toColumnId": column_id, "toIndex": 1}
    )
    assert response.status_code == 200
    updated_ids = response.json()["columns"][0]["cardIds"]
    assert updated_ids[0] == second_card_id
    assert updated_ids[1] == first_card_id


def test_move_card_between_columns(client: TestClient):
    board = client.get("/api/board").json()
    card_id = board["columns"][0]["cardIds"][0]
    target_column_id = board["columns"][1]["id"]

    response = client.post(
        f"/api/board/cards/{card_id}/move", json={"toColumnId": target_column_id, "toIndex": 0}
    )
    assert response.status_code == 200
    updated = response.json()
    assert card_id not in updated["columns"][0]["cardIds"]
    assert updated["columns"][1]["cardIds"][0] == card_id
    assert updated["cards"][card_id]["title"]


def test_move_card_persists_across_a_fresh_request(client: TestClient):
    # Regression test: move_card must actually commit its transaction. Checking
    # only the move response isn't enough — that response is generated on the
    # same DB connection/transaction that performed the move, so it would look
    # correct even if the change was never committed and silently rolled back
    # when the connection closed. Re-fetching with a separate request forces a
    # brand new connection, which only sees committed data.
    board = client.get("/api/board").json()
    card_id = board["columns"][0]["cardIds"][0]
    target_column_id = board["columns"][4]["id"]

    move_response = client.post(
        f"/api/board/cards/{card_id}/move", json={"toColumnId": target_column_id, "toIndex": 0}
    )
    assert move_response.status_code == 200

    refetched = client.get("/api/board").json()
    assert card_id not in refetched["columns"][0]["cardIds"]
    assert refetched["columns"][4]["cardIds"][0] == card_id


def test_move_missing_card_returns_404(client: TestClient):
    board = client.get("/api/board").json()
    column_id = board["columns"][0]["id"]

    response = client.post(
        "/api/board/cards/9999/move", json={"toColumnId": column_id, "toIndex": 0}
    )
    assert response.status_code == 404


def test_move_card_to_missing_column_returns_404(client: TestClient):
    board = client.get("/api/board").json()
    card_id = board["columns"][0]["cardIds"][0]

    response = client.post(
        f"/api/board/cards/{card_id}/move", json={"toColumnId": "9999", "toIndex": 0}
    )
    assert response.status_code == 404


def test_database_file_is_created_automatically_with_expected_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    db_path = tmp_path / "fresh.db"
    assert not db_path.exists()
    monkeypatch.setenv("PM_DB_PATH", str(db_path))

    with TestClient(app):
        pass

    assert db_path.exists()
    connection = sqlite3.connect(db_path)
    try:
        tables = {
            row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
    finally:
        connection.close()
    assert {"users", "boards", "columns", "cards"}.issubset(tables)


@pytest.fixture
def board_ctx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PM_DB_PATH", str(tmp_path / "ai_ops.db"))
    db.init_db()
    connection = db.get_connection()
    user_id = board.ensure_default_user(connection)
    board_id = board.get_or_create_board_id(connection, user_id)
    yield connection, board_id
    connection.close()


def test_apply_ai_operation_create_card(board_ctx):
    connection, board_id = board_ctx
    column_id = board.fetch_board(connection, board_id).columns[0].id

    board.apply_ai_operation(
        connection, board_id, AIOperation(op="create_card", columnId=column_id, title="De la IA")
    )

    updated = board.fetch_board(connection, board_id)
    assert any(card.title == "De la IA" for card in updated.cards.values())


def test_apply_ai_operation_missing_required_field_raises(board_ctx):
    connection, board_id = board_ctx

    with pytest.raises(ValueError):
        board.apply_ai_operation(connection, board_id, AIOperation(op="create_card"))


def test_apply_ai_operation_move_to_missing_card_raises_not_found(board_ctx):
    connection, board_id = board_ctx
    column_id = board.fetch_board(connection, board_id).columns[0].id

    with pytest.raises(board.NotFoundError):
        board.apply_ai_operation(
            connection,
            board_id,
            AIOperation(op="move_card", cardId="9999", toColumnId=column_id, toIndex=0),
        )
