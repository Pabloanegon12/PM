import type { Board } from "./types";

type MoveCardArgs = {
  cardId: string;
  fromColumnId: string;
  toColumnId: string;
  toIndex: number;
};

export function moveCardInBoard(board: Board, { cardId, fromColumnId, toColumnId, toIndex }: MoveCardArgs): Board {
  const columns = board.columns.map((column) => {
    if (column.id === fromColumnId && column.id === toColumnId) {
      const cardIds = column.cardIds.filter((id) => id !== cardId);
      cardIds.splice(toIndex, 0, cardId);
      return { ...column, cardIds };
    }
    if (column.id === fromColumnId) {
      return { ...column, cardIds: column.cardIds.filter((id) => id !== cardId) };
    }
    if (column.id === toColumnId) {
      const cardIds = [...column.cardIds];
      cardIds.splice(toIndex, 0, cardId);
      return { ...column, cardIds };
    }
    return column;
  });
  return { ...board, columns };
}
