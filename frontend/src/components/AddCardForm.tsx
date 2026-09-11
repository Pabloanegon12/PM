"use client";

import { useState, type FormEvent } from "react";

type AddCardFormProps = {
  onSubmit: (title: string, details: string) => void;
  onCancel: () => void;
};

export function AddCardForm({ onSubmit, onCancel }: AddCardFormProps) {
  const [title, setTitle] = useState("");
  const [details, setDetails] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmedTitle = title.trim();
    if (trimmedTitle === "") return;
    onSubmit(trimmedTitle, details.trim());
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-2 rounded-lg border border-gray-100 bg-white p-3 shadow-sm"
    >
      <input
        autoFocus
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        placeholder="Título de la tarjeta"
        aria-label="Título de la tarjeta"
        className="rounded-md border border-gray-200 px-2 py-1 text-sm text-navy outline-none focus:border-primary-blue focus:ring-1 focus:ring-primary-blue"
      />
      <textarea
        value={details}
        onChange={(event) => setDetails(event.target.value)}
        placeholder="Detalles"
        aria-label="Detalles"
        rows={2}
        className="resize-none rounded-md border border-gray-200 px-2 py-1 text-sm text-navy outline-none focus:border-primary-blue focus:ring-1 focus:ring-primary-blue"
      />
      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md px-3 py-1 text-sm text-muted-gray hover:text-navy"
        >
          Cancelar
        </button>
        <button
          type="submit"
          className="rounded-md bg-secondary-purple px-3 py-1 text-sm font-medium text-white hover:bg-secondary-purple-dark"
        >
          Añadir
        </button>
      </div>
    </form>
  );
}
