"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { Card } from "@/lib/types";
import { CardItem } from "./CardItem";

type SortableCardProps = {
  card: Card;
  onDelete: () => void;
  onEdit: (title: string, details: string) => void;
};

export function SortableCard({ card, onDelete, onEdit }: SortableCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: card.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <CardItem card={card} onDelete={onDelete} onEdit={onEdit} />
    </div>
  );
}
