import secrets

from fastapi import Cookie, HTTPException, Response, status

from app import chat

SESSION_COOKIE_NAME = "session_id"
USERNAME = "user"
PASSWORD = "password"

_sessions: set[str] = set()


def create_session(response: Response) -> None:
    session_id = secrets.token_urlsafe(32)
    _sessions.add(session_id)
    response.set_cookie(SESSION_COOKIE_NAME, session_id, httponly=True, samesite="lax")


def destroy_session(response: Response, session_id: str | None) -> None:
    if session_id is not None:
        _sessions.discard(session_id)
        chat.clear_history(session_id)
    response.delete_cookie(SESSION_COOKIE_NAME)


def require_session(
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> str:
    if session_id is None or session_id not in _sessions:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return session_id
