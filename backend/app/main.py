import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Cookie, Depends, FastAPI, HTTPException, Response, status
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import ai, board, chat
from app.auth import (
    PASSWORD,
    SESSION_COOKIE_NAME,
    USERNAME,
    create_session,
    destroy_session,
    require_session,
)
from app.db import get_connection, get_db, init_db
from app.schemas import (
    AIChatRequest,
    AIChatResponse,
    AIOperation,
    AITestResponse,
    Board,
    ChatMessage,
    CreateCardRequest,
    MoveCardRequest,
    RenameColumnRequest,
    UpdateCardRequest,
)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


def require_board(
    connection: sqlite3.Connection = Depends(get_db),
    _session_id: str = Depends(require_session),
) -> tuple[sqlite3.Connection, int]:
    user_id = board.ensure_default_user(connection)
    board_id = board.get_or_create_board_id(connection, user_id)
    return connection, board_id


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/login")
def login(credentials: LoginRequest, response: Response) -> dict[str, str]:
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    create_session(response)
    return {"status": "ok"}


@app.post("/api/logout")
def logout(
    response: Response,
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> dict[str, str]:
    destroy_session(response, session_id)
    return {"status": "ok"}


@app.get("/api/me")
def me(session_id: str = Depends(require_session)) -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/board")
def get_board(board_ctx: tuple[sqlite3.Connection, int] = Depends(require_board)) -> Board:
    connection, board_id = board_ctx
    return board.fetch_board(connection, board_id)


@app.post("/api/board/cards")
def create_card(
    payload: CreateCardRequest, board_ctx: tuple[sqlite3.Connection, int] = Depends(require_board)
) -> Board:
    connection, board_id = board_ctx
    try:
        board.add_card(connection, board_id, payload.columnId, payload.title, payload.details)
    except board.NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    return board.fetch_board(connection, board_id)


@app.patch("/api/board/cards/{card_id}")
def edit_card(
    card_id: str,
    payload: UpdateCardRequest,
    board_ctx: tuple[sqlite3.Connection, int] = Depends(require_board),
) -> Board:
    connection, board_id = board_ctx
    try:
        board.update_card(connection, board_id, card_id, payload.title, payload.details)
    except board.NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    return board.fetch_board(connection, board_id)


@app.delete("/api/board/cards/{card_id}")
def remove_card(
    card_id: str, board_ctx: tuple[sqlite3.Connection, int] = Depends(require_board)
) -> Board:
    connection, board_id = board_ctx
    try:
        board.delete_card(connection, board_id, card_id)
    except board.NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return board.fetch_board(connection, board_id)


@app.patch("/api/board/columns/{column_id}")
def rename_column(
    column_id: str,
    payload: RenameColumnRequest,
    board_ctx: tuple[sqlite3.Connection, int] = Depends(require_board),
) -> Board:
    connection, board_id = board_ctx
    try:
        board.rename_column(connection, board_id, column_id, payload.name)
    except board.NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error
    return board.fetch_board(connection, board_id)


@app.post("/api/board/cards/{card_id}/move")
def move_card(
    card_id: str,
    payload: MoveCardRequest,
    board_ctx: tuple[sqlite3.Connection, int] = Depends(require_board),
) -> Board:
    connection, board_id = board_ctx
    try:
        board.move_card(connection, board_id, card_id, payload.toColumnId, payload.toIndex)
    except board.NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return board.fetch_board(connection, board_id)


@app.post("/api/ai/test")
async def test_ai(_session_id: str = Depends(require_session)) -> AITestResponse:
    try:
        answer = await ai.ask("¿Cuánto es 2+2? Responde solo con el número.")
    except ai.AIError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    return AITestResponse(answer=answer)


def _load_board_for_ai(session_id: str) -> tuple[int, Board]:
    connection = get_connection()
    try:
        user_id = board.ensure_default_user(connection)
        board_id = board.get_or_create_board_id(connection, user_id)
        return board_id, board.fetch_board(connection, board_id)
    finally:
        connection.close()


def _apply_ai_operations(board_id: int, operations: list[AIOperation]) -> Board:
    connection = get_connection()
    try:
        for operation in operations:
            board.apply_ai_operation(connection, board_id, operation)
        return board.fetch_board(connection, board_id)
    finally:
        connection.close()


@app.post("/api/ai/chat")
async def ai_chat(
    payload: AIChatRequest,
    session_id: str = Depends(require_session),
) -> AIChatResponse:
    # Each helper above opens and closes its own SQLite connection within a
    # single run_in_threadpool call (not via Depends), because this route is
    # async and awaits the AI call in between: a connection created by a sync
    # dependency can end up on a different thread than where it's later used.
    board_id, current_board = await run_in_threadpool(_load_board_for_ai, session_id)
    history = chat.get_history(session_id)

    try:
        result = await ai.chat(current_board, history, payload.message)
    except ai.AIError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

    operations = [AIOperation.model_validate(op) for op in result["operations"]]
    try:
        updated_board = await run_in_threadpool(_apply_ai_operations, board_id, operations)
    except (board.NotFoundError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error

    chat.append_message(session_id, ChatMessage(role="user", content=payload.message))
    chat.append_message(session_id, ChatMessage(role="assistant", content=result["message"]))

    return AIChatResponse(message=result["message"], board=updated_board)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
