import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app import board
from app.auth import require_session
from app.db import get_db
from app.schemas import (
    Board,
    CreateCardRequest,
    MoveCardRequest,
    RenameColumnRequest,
    UpdateCardRequest,
)

router = APIRouter(prefix="/api/board", tags=["board"])


def require_board(
    connection: sqlite3.Connection = Depends(get_db),
    _session_id: str = Depends(require_session),
) -> tuple[sqlite3.Connection, int]:
    user_id = board.ensure_default_user(connection)
    board_id = board.get_or_create_board_id(connection, user_id)
    return connection, board_id


@router.get("")
def get_board(board_ctx: tuple[sqlite3.Connection, int] = Depends(require_board)) -> Board:
    connection, board_id = board_ctx
    return board.fetch_board(connection, board_id)


@router.post("/cards")
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


@router.patch("/cards/{card_id}")
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


@router.delete("/cards/{card_id}")
def remove_card(
    card_id: str, board_ctx: tuple[sqlite3.Connection, int] = Depends(require_board)
) -> Board:
    connection, board_id = board_ctx
    try:
        board.delete_card(connection, board_id, card_id)
    except board.NotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return board.fetch_board(connection, board_id)


@router.patch("/columns/{column_id}")
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


@router.post("/cards/{card_id}/move")
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
