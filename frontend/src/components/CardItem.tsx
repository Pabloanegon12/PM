"use client";

import { useState, type FormEvent } from "react";
import type { Card } from "@/lib/types";

type CardItemProps = {
  card: Card;
  onDelete: () => void;
  onEdit: (title: string, details: string) => void;
};

export function CardItem({ card, onDelete, onEdit }: CardItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [titleDraft, setTitleDraft] = useState(card.title);
  const [detailsDraft, setDetailsDraft] = useState(card.details);

  function startEdit() {
    setTitleDraft(card.title);
    setDetailsDraft(card.details);
    setIsEditing(true);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmedTitle = titleDraft.trim();
    if (trimmedTitle === "") return;
    onEdit(trimmedTitle, detailsDraft.trim());
    setIsEditing(false);
  }

  if (isEditing) {
    return (
      <form
        onSubmit={handleSubmit}
        onPointerDown={(event) => event.stopPropagation()}
        onKeyDown={(event) => event.stopPropagation()}
        className="flex flex-col gap-2 rounded-lg border border-primary-blue bg-white p-3 shadow-sm"
      >
        <input
          autoFocus
          value={titleDraft}
          onChange={(event) => setTitleDraft(event.target.value)}
          aria-label={`Título de ${card.title}`}
          className="rounded-md border border-gray-200 px-2 py-1 text-sm text-navy outline-none focus:border-primary-blue focus:ring-1 focus:ring-primary-blue"
        />
        <textarea
          value={detailsDraft}
          onChange={(event) => setDetailsDraft(event.target.value)}
          aria-label={`Detalles de ${card.title}`}
          rows={2}
          className="resize-none rounded-md border border-gray-200 px-2 py-1 text-sm text-navy outline-none focus:border-primary-blue focus:ring-1 focus:ring-primary-blue"
        />
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={() => setIsEditing(false)}
            className="rounded-md px-3 py-1 text-sm text-muted-gray hover:text-navy"
          >
            Cancelar
          </button>
          <button
            type="submit"
            className="rounded-md bg-secondary-purple px-3 py-1 text-sm font-medium text-white hover:bg-secondary-purple-dark"
          >
            Guardar
          </button>
        </div>
      </form>
    );
  }

  return (
    <div className="group relative rounded-lg border border-gray-100 bg-white p-3 shadow-sm transition-shadow hover:shadow-md">
      <div
        className="absolute right-2 top-2 flex gap-2 opacity-0 transition-opacity focus-within:opacity-100 group-hover:opacity-100"
        onPointerDown={(event) => event.stopPropagation()}
        onKeyDown={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          onClick={startEdit}
          aria-label={`Editar tarjeta ${card.title}`}
          className="text-muted-gray hover:text-primary-blue"
        >
          ✎
        </button>
        <button
          type="button"
          onClick={onDelete}
          aria-label={`Eliminar tarjeta ${card.title}`}
          className="text-muted-gray hover:text-red-600"
        >
          ×
        </button>
      </div>
      <p className="pr-10 text-sm font-medium text-navy">{card.title}</p>
      <p className="mt-1 line-clamp-2 text-xs text-muted-gray">{card.details}</p>
    </div>
  );
}
