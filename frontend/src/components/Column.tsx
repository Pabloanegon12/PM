"use client";

import { useState } from "react";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Card, Column as ColumnType } from "@/lib/types";
import { SortableCard } from "./SortableCard";
import { AddCardForm } from "./AddCardForm";

type ColumnProps = {
  column: ColumnType;
  cards: Card[];
  onAddCard: (columnId: string, title: string, details: string) => void;
  onEditCard: (cardId: string, title: string, details: string) => void;
  onDeleteCard: (cardId: string) => void;
  onRenameColumn: (columnId: string, name: string) => void;
};

export function Column({ column, cards, onAddCard, onEditCard, onDeleteCard, onRenameColumn }: ColumnProps) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [nameDraft, setNameDraft] = useState(column.name);
  const [isAddingCard, setIsAddingCard] = useState(false);
  const { setNodeRef, isOver } = useDroppable({ id: column.id });

  function startRename() {
    setNameDraft(column.name);
    setIsEditingName(true);
  }

  function commitRename() {
    onRenameColumn(column.id, nameDraft);
    setIsEditingName(false);
  }

  function cancelRename() {
    setNameDraft(column.name);
    setIsEditingName(false);
  }

  function handleAddCard(title: string, details: string) {
    onAddCard(column.id, title, details);
    setIsAddingCard(false);
  }

  return (
    <div className="flex w-72 shrink-0 flex-col rounded-xl bg-white shadow-sm">
      <div className="flex items-center justify-between gap-2 px-4 pt-4 pb-3">
        {isEditingName ? (
          <input
            autoFocus
            value={nameDraft}
            onChange={(event) => setNameDraft(event.target.value)}
            onBlur={commitRename}
            onKeyDown={(event) => {
              if (event.key === "Enter") commitRename();
              if (event.key === "Escape") cancelRename();
            }}
            aria-label="Nombre de la columna"
            className="w-full rounded-md border border-primary-blue px-2 py-1 text-sm font-semibold text-navy outline-none focus:ring-2 focus:ring-primary-blue"
          />
        ) : (
          <button
            type="button"
            onClick={startRename}
            className="truncate text-left text-sm font-semibold text-navy hover:text-primary-blue"
          >
            {column.name}
          </button>
        )}
        <span className="shrink-0 text-xs text-muted-gray">{cards.length}</span>
      </div>

      <div
        ref={setNodeRef}
        className={`flex flex-col gap-3 rounded-lg px-4 pb-3 transition-colors ${
          isOver ? "bg-accent-yellow/10 ring-2 ring-accent-yellow" : ""
        }`}
      >
        <SortableContext items={cards.map((card) => card.id)} strategy={verticalListSortingStrategy}>
          {cards.map((card) => (
            <SortableCard
              key={card.id}
              card={card}
              onDelete={() => onDeleteCard(card.id)}
              onEdit={(title, details) => onEditCard(card.id, title, details)}
            />
          ))}
        </SortableContext>
      </div>

      <div className="px-4 pb-4">
        {isAddingCard ? (
          <AddCardForm onSubmit={handleAddCard} onCancel={() => setIsAddingCard(false)} />
        ) : (
          <button
            type="button"
            onClick={() => setIsAddingCard(true)}
            className="w-full rounded-md px-2 py-2 text-left text-sm text-primary-blue hover:bg-primary-blue/10"
          >
            + Añadir tarjeta
          </button>
        )}
      </div>
    </div>
  );
}
