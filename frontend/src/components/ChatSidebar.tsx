"use client";

import { useState, type FormEvent } from "react";
import { chatWithAI } from "@/lib/api";
import type { Board } from "@/lib/types";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type ChatSidebarProps = {
  onBoardUpdate: (board: Board) => void;
};

export function ChatSidebar({ onBoardUpdate }: ChatSidebarProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = input.trim();
    if (trimmed === "" || isSending) return;

    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const result = await chatWithAI(trimmed);
      setMessages((current) => [...current, { role: "assistant", content: result.message }]);
      onBoardUpdate(result.board);
    } catch {
      setError("No se ha podido contactar con la IA.");
    } finally {
      setIsSending(false);
    }
  }

  return (
    <aside className="flex w-80 shrink-0 flex-col border-l border-gray-100 bg-white">
      <div className="border-b-2 border-accent-yellow px-4 py-3">
        <h2 className="text-sm font-bold text-navy">Asistente IA</h2>
      </div>

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-3">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
              message.role === "user"
                ? "self-end bg-primary-blue text-white"
                : "self-start bg-gray-100 text-navy"
            }`}
          >
            {message.content}
          </div>
        ))}
        {isSending ? (
          <div className="self-start rounded-lg bg-gray-100 px-3 py-2 text-sm text-muted-gray">
            IA escribiendo…
          </div>
        ) : null}
      </div>

      {error ? <p className="px-4 pb-2 text-sm text-red-600">{error}</p> : null}

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-gray-100 p-3">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Escribe un mensaje…"
          disabled={isSending}
          className="flex-1 rounded-md border border-gray-200 px-3 py-2 text-sm text-navy outline-none focus:border-primary-blue focus:ring-1 focus:ring-primary-blue disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={isSending}
          className="rounded-md bg-secondary-purple px-3 py-2 text-sm font-medium text-white hover:bg-secondary-purple-dark disabled:opacity-60"
        >
          Enviar
        </button>
      </form>
    </aside>
  );
}
