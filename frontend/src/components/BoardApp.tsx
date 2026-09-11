"use client";

import { useEffect, useState } from "react";
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { createCard, deleteCard, fetchBoard, moveCard, renameColumn, updateCard } from "@/lib/api";
import { moveCardInBoard } from "@/lib/boardDrag";
import type { Board as BoardType } from "@/lib/types";
import { Board } from "./Board";
import { CardItem } from "./CardItem";
import { ChatSidebar } from "./ChatSidebar";

function findColumnId(board: BoardType, id: string): string | undefined {
  if (board.columns.some((column) => column.id === id)) return id;
  return board.columns.find((column) => column.cardIds.includes(id))?.id;
}

type BoardAppProps = {
  onLogout: () => void;
};

export function BoardApp({ onLogout }: BoardAppProps) {
  const [board, setBoard] = useState<BoardType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);

  useEffect(() => {
    fetchBoard()
      .then(setBoard)
      .catch(() => setError("No se ha podido cargar el tablero."));
  }, []);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  async function handleLogout() {
    await fetch("/api/logout", { method: "POST", credentials: "include" });
    onLogout();
  }

  async function handleAddCard(columnId: string, title: string, details: string) {
    try {
      setBoard(await createCard(columnId, title, details));
    } catch {
      setError("No se ha podido añadir la tarjeta.");
    }
  }

  async function handleEditCard(cardId: string, title: string, details: string) {
    try {
      setBoard(await updateCard(cardId, title, details));
    } catch {
      setError("No se ha podido editar la tarjeta.");
    }
  }

  async function handleDeleteCard(cardId: string) {
    try {
      setBoard(await deleteCard(cardId));
    } catch {
      setError("No se ha podido eliminar la tarjeta.");
    }
  }

  async function handleRenameColumn(columnId: string, name: string) {
    try {
      setBoard(await renameColumn(columnId, name));
    } catch {
      setError("No se ha podido renombrar la columna.");
    }
  }

  function handleDragStart(event: DragStartEvent) {
    setActiveCardId(String(event.active.id));
  }

  function handleDragOver(event: DragOverEvent) {
    const { active, over } = event;
    if (!over || !board) return;
    const activeId = String(active.id);
    const overId = String(over.id);
    if (activeId === overId) return;

    const fromColumnId = findColumnId(board, activeId);
    const toColumnId = findColumnId(board, overId);
    if (!fromColumnId || !toColumnId || fromColumnId === toColumnId) return;

    const toColumn = board.columns.find((column) => column.id === toColumnId);
    if (!toColumn) return;
    const overIndex = toColumn.cardIds.indexOf(overId);
    const toIndex = overIndex >= 0 ? overIndex : toColumn.cardIds.length;

    setBoard(moveCardInBoard(board, { cardId: activeId, fromColumnId, toColumnId, toIndex }));
  }

  async function handleDragEnd(event: DragEndEvent) {
    setActiveCardId(null);
    const { active, over } = event;
    if (!board) return;
    const activeId = String(active.id);

    // The card may already have been relocated locally by handleDragOver, so
    // persist wherever it currently sits rather than relying on `over` alone
    // (which, after that relocation, can end up pointing at the dragged card
    // itself).
    const columnId = findColumnId(board, activeId);
    if (!columnId) return;
    const column = board.columns.find((c) => c.id === columnId);
    if (!column) return;

    let toIndex = column.cardIds.indexOf(activeId);
    if (over) {
      const overId = String(over.id);
      const overIndex = column.cardIds.indexOf(overId);
      if (overId !== activeId && overIndex >= 0) {
        toIndex = overIndex;
      }
    }
    if (toIndex < 0) return;

    try {
      setBoard(await moveCard(activeId, columnId, toIndex));
    } catch {
      setError("No se ha podido mover la tarjeta.");
    }
  }

  const activeCard = activeCardId && board ? board.cards[activeCardId] : null;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between border-b-2 border-accent-yellow bg-white px-6 py-4 shadow-sm">
        <h1 className="text-xl font-bold text-navy">Curso Claude</h1>
        <button
          type="button"
          onClick={handleLogout}
          className="text-sm text-muted-gray hover:text-navy"
        >
          Cerrar sesión
        </button>
      </header>
      {error ? <p className="px-6 py-2 text-sm text-red-600">{error}</p> : null}
      <div className="flex flex-1 overflow-hidden">
        {!board ? (
          <p className="px-6 py-4 text-sm text-muted-gray">Cargando tablero…</p>
        ) : (
          <>
            <DndContext
              id="board-dnd-context"
              sensors={sensors}
              collisionDetection={closestCorners}
              onDragStart={handleDragStart}
              onDragOver={handleDragOver}
              onDragEnd={handleDragEnd}
            >
              <Board
                board={board}
                onAddCard={handleAddCard}
                onEditCard={handleEditCard}
                onDeleteCard={handleDeleteCard}
                onRenameColumn={handleRenameColumn}
              />
              <DragOverlay>
                {activeCard ? (
                  <div className="w-64 rotate-2 shadow-lg">
                    <CardItem card={activeCard} onDelete={() => {}} onEdit={() => {}} />
                  </div>
                ) : null}
              </DragOverlay>
            </DndContext>
            <ChatSidebar onBoardUpdate={setBoard} />
          </>
        )}
      </div>
    </div>
  );
}
