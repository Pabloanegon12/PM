from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError

from app import ai, board, chat
from app.auth import require_session
from app.db import get_connection
from app.schemas import (
    AIChatRequest,
    AIChatResponse,
    AIOperation,
    AITestResponse,
    Board,
    ChatMessage,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/test")
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


def _apply_ai_operations(board_id: int, current_board: Board, operations: list[AIOperation]) -> Board:
    # Validate every operation against the pre-AI board snapshot before applying any
    # of them: each mutation in app/board.py commits its own transaction, so without
    # this pass an invalid operation later in the batch would leave earlier ones
    # permanently persisted even though the whole request reports an error.
    for operation in operations:
        board.validate_ai_operation(current_board, operation)

    connection = get_connection()
    try:
        for operation in operations:
            board.apply_ai_operation(connection, board_id, operation)
        return board.fetch_board(connection, board_id)
    finally:
        connection.close()


@router.post("/chat")
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

    try:
        operations = [AIOperation.model_validate(op) for op in result["operations"]]
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"La IA devolvió una operación con formato inválido: {error}",
        ) from error

    try:
        updated_board = await run_in_threadpool(
            _apply_ai_operations, board_id, current_board, operations
        )
    except (board.NotFoundError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)) from error

    chat.append_message(session_id, ChatMessage(role="user", content=payload.message))
    chat.append_message(session_id, ChatMessage(role="assistant", content=result["message"]))

    return AIChatResponse(message=result["message"], board=updated_board)
