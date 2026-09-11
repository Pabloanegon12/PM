from typing import Literal

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class Card(BaseModel):
    id: str
    title: str
    details: str


class Column(BaseModel):
    id: str
    name: str
    cardIds: list[str]


class Board(BaseModel):
    columns: list[Column]
    cards: dict[str, Card]


class CreateCardRequest(BaseModel):
    columnId: str
    title: str
    details: str = ""


class UpdateCardRequest(BaseModel):
    title: str
    details: str = ""


class RenameColumnRequest(BaseModel):
    name: str


class MoveCardRequest(BaseModel):
    toColumnId: str
    toIndex: int


class AITestResponse(BaseModel):
    answer: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AIChatRequest(BaseModel):
    message: str


class AIOperation(BaseModel):
    op: Literal["create_card", "update_card", "delete_card", "rename_column", "move_card"]
    columnId: str | None = None
    cardId: str | None = None
    title: str | None = None
    details: str | None = None
    name: str | None = None
    toColumnId: str | None = None
    toIndex: int | None = None


class AIChatResponse(BaseModel):
    message: str
    board: Board
