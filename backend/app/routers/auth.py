from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.auth import (
    PASSWORD,
    SESSION_COOKIE_NAME,
    USERNAME,
    create_session,
    destroy_session,
    require_session,
)
from app.schemas import LoginRequest

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login")
def login(credentials: LoginRequest, response: Response) -> dict[str, str]:
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    create_session(response)
    return {"status": "ok"}


@router.post("/logout")
def logout(
    response: Response,
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> dict[str, str]:
    destroy_session(response, session_id)
    return {"status": "ok"}


@router.get("/me")
def me(session_id: str = Depends(require_session)) -> dict[str, str]:
    return {"status": "ok"}
