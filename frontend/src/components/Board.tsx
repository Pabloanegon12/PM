import type { Board as BoardType } from "@/lib/types";
import { Column } from "./Column";

type BoardProps = {
  board: BoardType;
  onAddCard: (columnId: string, title: string, details: string) => void;
  onEditCard: (cardId: string, title: string, details: string) => void;
  onDeleteCard: (cardId: string) => void;
  onRenameColumn: (columnId: string, name: string) => void;
};

export function Board({ board, onAddCard, onEditCard, onDeleteCard, onRenameColumn }: BoardProps) {
  return (
    <div className="flex-1 overflow-x-auto">
      <div className="flex min-h-full items-start gap-6 p-6">
        {board.columns.map((column) => (
          <Column
            key={column.id}
            column={column}
            cards={column.cardIds.map((cardId) => board.cards[cardId])}
            onAddCard={onAddCard}
            onEditCard={onEditCard}
            onDeleteCard={onDeleteCard}
            onRenameColumn={onRenameColumn}
          />
        ))}
      </div>
    </div>
  );
}
