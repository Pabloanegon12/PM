from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routers import ai, auth, board, health

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(board.router)
app.include_router(ai.router)

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
