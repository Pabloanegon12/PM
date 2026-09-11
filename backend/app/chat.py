from app.schemas import ChatMessage

_histories: dict[str, list[ChatMessage]] = {}


def get_history(session_id: str) -> list[ChatMessage]:
    return _histories.setdefault(session_id, [])


def append_message(session_id: str, message: ChatMessage) -> None:
    get_history(session_id).append(message)


def clear_history(session_id: str) -> None:
    _histories.pop(session_id, None)
