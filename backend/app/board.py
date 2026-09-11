import sqlite3

from app.schemas import AIOperation, Board, Card, Column

DEFAULT_USERNAME = "user"

SEED_COLUMNS = [
    {
        "name": "Backlog",
        "cards": [
            {
                "title": "Definir arquitectura del backend",
                "details": "Evaluar si conviene una API REST o GraphQL y documentar la decisión.",
            },
            {
                "title": "Investigar proveedores de hosting",
                "details": "Comparar precios y facilidad de despliegue entre Vercel, Railway y Render.",
            },
        ],
    },
    {
        "name": "Por hacer",
        "cards": [
            {
                "title": "Diseñar esquema de base de datos",
                "details": "Modelar las tablas principales y sus relaciones antes de escribir migraciones.",
            },
            {
                "title": "Configurar entorno de desarrollo",
                "details": "Documentar los pasos para que cualquier persona del equipo pueda arrancar el proyecto en local.",
            },
        ],
    },
    {
        "name": "En curso",
        "cards": [
            {
                "title": "Implementar autenticación de usuarios",
                "details": "Añadir inicio de sesión con email y contraseña, con validación en el servidor.",
            },
            {
                "title": "Maquetar página de inicio",
                "details": "Traducir el diseño de Figma a componentes reutilizables.",
            },
        ],
    },
    {
        "name": "En revisión",
        "cards": [
            {
                "title": "Revisar pull request de la API de pagos",
                "details": "Comprobar el manejo de errores y que los importes se redondean correctamente.",
            },
        ],
    },
    {
        "name": "Hecho",
        "cards": [
            {
                "title": "Configurar repositorio en GitHub",
                "details": "Crear el repositorio, proteger la rama principal y añadir la plantilla de pull requests.",
            },
            {
                "title": "Redactar documento de requisitos",
                "details": "Recoger el alcance del MVP y compartirlo con el equipo para validarlo.",
            },
        ],
    },
]


class NotFoundError(Exception):
    pass


def _to_int_id(value: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise NotFoundError("Identificador inválido") from error


def ensure_default_user(connection: sqlite3.Connection) -> int:
    row = connection.execute(
        "SELECT id FROM users WHERE username = ?", (DEFAULT_USERNAME,)
    ).fetchone()
    if row is not None:
        return row["id"]

    connection.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (DEFAULT_USERNAME,))
    connection.commit()
    row = connection.execute(
        "SELECT id FROM users WHERE username = ?", (DEFAULT_USERNAME,)
    ).fetchone()
    return row["id"]


def get_or_create_board_id(connection: sqlite3.Connection, user_id: int) -> int:
    row = connection.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)).fetchone()
    if row is not None:
        return row["id"]

    cursor = connection.execute("INSERT INTO boards (user_id) VALUES (?)", (user_id,))
    board_id = cursor.lastrowid

    for column_position, column in enumerate(SEED_COLUMNS):
        column_cursor = connection.execute(
            "INSERT INTO columns (board_id, name, position) VALUES (?, ?, ?)",
            (board_id, column["name"], column_position),
        )
        column_id = column_cursor.lastrowid
        for card_position, card in enumerate(column["cards"]):
            connection.execute(
                "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
                (column_id, card["title"], card["details"], card_position),
            )

    connection.commit()
    return board_id


def fetch_board(connection: sqlite3.Connection, board_id: int) -> Board:
    column_rows = connection.execute(
        "SELECT id, name FROM columns WHERE board_id = ? ORDER BY position", (board_id,)
    ).fetchall()

    columns: list[Column] = []
    cards: dict[str, Card] = {}
    for column_row in column_rows:
        column_id = str(column_row["id"])
        card_rows = connection.execute(
            "SELECT id, title, details FROM cards WHERE column_id = ? ORDER BY position",
            (column_row["id"],),
        ).fetchall()
        card_ids: list[str] = []
        for card_row in card_rows:
            card_id = str(card_row["id"])
            card_ids.append(card_id)
            cards[card_id] = Card(id=card_id, title=card_row["title"], details=card_row["details"])
        columns.append(Column(id=column_id, name=column_row["name"], cardIds=card_ids))

    return Board(columns=columns, cards=cards)


def _get_column_in_board(connection: sqlite3.Connection, board_id: int, column_id: str) -> int:
    column_id_int = _to_int_id(column_id)
    row = connection.execute(
        "SELECT id FROM columns WHERE id = ? AND board_id = ?", (column_id_int, board_id)
    ).fetchone()
    if row is None:
        raise NotFoundError("Columna no encontrada")
    return column_id_int


def _get_card_in_board(connection: sqlite3.Connection, board_id: int, card_id: str) -> tuple[int, int]:
    card_id_int = _to_int_id(card_id)
    row = connection.execute(
        """
        SELECT cards.id, cards.column_id FROM cards
        JOIN columns ON columns.id = cards.column_id
        WHERE cards.id = ? AND columns.board_id = ?
        """,
        (card_id_int, board_id),
    ).fetchone()
    if row is None:
        raise NotFoundError("Tarjeta no encontrada")
    return card_id_int, row["column_id"]


def add_card(connection: sqlite3.Connection, board_id: int, column_id: str, title: str, details: str) -> None:
    column_id_int = _get_column_in_board(connection, board_id, column_id)
    trimmed_title = title.strip()
    if trimmed_title == "":
        raise ValueError("El título de la tarjeta no puede estar vacío")

    max_position_row = connection.execute(
        "SELECT COALESCE(MAX(position), -1) AS max_position FROM cards WHERE column_id = ?",
        (column_id_int,),
    ).fetchone()
    next_position = max_position_row["max_position"] + 1
    connection.execute(
        "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
        (column_id_int, trimmed_title, details.strip(), next_position),
    )
    connection.commit()


def update_card(connection: sqlite3.Connection, board_id: int, card_id: str, title: str, details: str) -> None:
    card_id_int, _column_id = _get_card_in_board(connection, board_id, card_id)
    trimmed_title = title.strip()
    if trimmed_title == "":
        raise ValueError("El título de la tarjeta no puede estar vacío")

    connection.execute(
        "UPDATE cards SET title = ?, details = ? WHERE id = ?",
        (trimmed_title, details.strip(), card_id_int),
    )
    connection.commit()


def delete_card(connection: sqlite3.Connection, board_id: int, card_id: str) -> None:
    card_id_int, _column_id = _get_card_in_board(connection, board_id, card_id)
    connection.execute("DELETE FROM cards WHERE id = ?", (card_id_int,))
    connection.commit()


def rename_column(connection: sqlite3.Connection, board_id: int, column_id: str, name: str) -> None:
    column_id_int = _get_column_in_board(connection, board_id, column_id)
    trimmed_name = name.strip()
    if trimmed_name == "":
        raise ValueError("El nombre de la columna no puede estar vacío")

    connection.execute("UPDATE columns SET name = ? WHERE id = ?", (trimmed_name, column_id_int))
    connection.commit()


def _set_column_order(connection: sqlite3.Connection, column_id: int, ordered_card_ids: list[int]) -> None:
    for index, card_id in enumerate(ordered_card_ids):
        connection.execute(
            "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
            (column_id, index, card_id),
        )


def move_card(
    connection: sqlite3.Connection, board_id: int, card_id: str, to_column_id: str, to_index: int
) -> None:
    card_id_int, from_column_id = _get_card_in_board(connection, board_id, card_id)
    to_column_id_int = _get_column_in_board(connection, board_id, to_column_id)

    dest_rows = connection.execute(
        "SELECT id FROM cards WHERE column_id = ? AND id != ? ORDER BY position",
        (to_column_id_int, card_id_int),
    ).fetchall()
    dest_ids = [row["id"] for row in dest_rows]
    clamped_index = max(0, min(to_index, len(dest_ids)))
    dest_ids.insert(clamped_index, card_id_int)
    _set_column_order(connection, to_column_id_int, dest_ids)

    if from_column_id != to_column_id_int:
        source_rows = connection.execute(
            "SELECT id FROM cards WHERE column_id = ? ORDER BY position", (from_column_id,)
        ).fetchall()
        _set_column_order(connection, from_column_id, [row["id"] for row in source_rows])

    connection.commit()


def validate_ai_operation(current_board: Board, operation: AIOperation) -> None:
    """Check required fields and that referenced ids exist in `current_board`.

    Called for every operation in a batch before any of them is applied, so an
    invalid operation later in the batch can't leave earlier ones committed.
    """
    column_ids = {column.id for column in current_board.columns}
    card_ids = set(current_board.cards)

    if operation.op == "create_card":
        if operation.columnId is None or operation.title is None:
            raise ValueError("create_card requiere columnId y title")
        if operation.columnId not in column_ids:
            raise NotFoundError("Columna no encontrada")
    elif operation.op == "update_card":
        if operation.cardId is None or operation.title is None:
            raise ValueError("update_card requiere cardId y title")
        if operation.cardId not in card_ids:
            raise NotFoundError("Tarjeta no encontrada")
    elif operation.op == "delete_card":
        if operation.cardId is None:
            raise ValueError("delete_card requiere cardId")
        if operation.cardId not in card_ids:
            raise NotFoundError("Tarjeta no encontrada")
    elif operation.op == "rename_column":
        if operation.columnId is None or operation.name is None:
            raise ValueError("rename_column requiere columnId y name")
        if operation.columnId not in column_ids:
            raise NotFoundError("Columna no encontrada")
    elif operation.op == "move_card":
        if operation.cardId is None or operation.toColumnId is None or operation.toIndex is None:
            raise ValueError("move_card requiere cardId, toColumnId y toIndex")
        if operation.cardId not in card_ids:
            raise NotFoundError("Tarjeta no encontrada")
        if operation.toColumnId not in column_ids:
            raise NotFoundError("Columna no encontrada")


def apply_ai_operation(connection: sqlite3.Connection, board_id: int, operation: AIOperation) -> None:
    if operation.op == "create_card":
        if operation.columnId is None or operation.title is None:
            raise ValueError("create_card requiere columnId y title")
        add_card(connection, board_id, operation.columnId, operation.title, operation.details or "")
    elif operation.op == "update_card":
        if operation.cardId is None or operation.title is None:
            raise ValueError("update_card requiere cardId y title")
        update_card(connection, board_id, operation.cardId, operation.title, operation.details or "")
    elif operation.op == "delete_card":
        if operation.cardId is None:
            raise ValueError("delete_card requiere cardId")
        delete_card(connection, board_id, operation.cardId)
    elif operation.op == "rename_column":
        if operation.columnId is None or operation.name is None:
            raise ValueError("rename_column requiere columnId y name")
        rename_column(connection, board_id, operation.columnId, operation.name)
    elif operation.op == "move_card":
        if operation.cardId is None or operation.toColumnId is None or operation.toIndex is None:
            raise ValueError("move_card requiere cardId, toColumnId y toIndex")
        move_card(connection, board_id, operation.cardId, operation.toColumnId, operation.toIndex)
