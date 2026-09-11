import secrets
import time

from fastapi import Cookie, HTTPException, Response, status

from app import chat

SESSION_COOKIE_NAME = "session_id"
USERNAME = "user"
PASSWORD = "password"
SESSION_TTL_SECONDS = 24 * 60 * 60

_sessions: dict[str, float] = {}


def _evict_expired_sessions() -> None:
    now = time.time()
    expired = [
        session_id
        for session_id, created_at in _sessions.items()
        if now - created_at > SESSION_TTL_SECONDS
    ]
    for session_id in expired:
        _sessions.pop(session_id, None)
        chat.clear_history(session_id)


def create_session(response: Response) -> None:
    _evict_expired_sessions()
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = time.time()
    response.set_cookie(SESSION_COOKIE_NAME, session_id, httponly=True, samesite="lax")


def destroy_session(response: Response, session_id: str | None) -> None:
    if session_id is not None:
        _sessions.pop(session_id, None)
        chat.clear_history(session_id)
    response.delete_cookie(SESSION_COOKIE_NAME)


def require_session(
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> str:
    _evict_expired_sessions()
    if session_id is None or session_id not in _sessions:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return session_id
