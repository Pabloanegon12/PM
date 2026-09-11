import type { Board } from "./types";

async function request<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Error ${response.status} en ${input}`);
  }
  return response.json() as Promise<T>;
}

export function fetchBoard(): Promise<Board> {
  return request<Board>("/api/board");
}

export function createCard(columnId: string, title: string, details: string): Promise<Board> {
  return request<Board>("/api/board/cards", {
    method: "POST",
    body: JSON.stringify({ columnId, title, details }),
  });
}

export function updateCard(cardId: string, title: string, details: string): Promise<Board> {
  return request<Board>(`/api/board/cards/${cardId}`, {
    method: "PATCH",
    body: JSON.stringify({ title, details }),
  });
}

export function deleteCard(cardId: string): Promise<Board> {
  return request<Board>(`/api/board/cards/${cardId}`, { method: "DELETE" });
}

export function renameColumn(columnId: string, name: string): Promise<Board> {
  return request<Board>(`/api/board/columns/${columnId}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export function moveCard(cardId: string, toColumnId: string, toIndex: number): Promise<Board> {
  return request<Board>(`/api/board/cards/${cardId}/move`, {
    method: "POST",
    body: JSON.stringify({ toColumnId, toIndex }),
  });
}

export type ChatResult = {
  message: string;
  board: Board;
};

export function chatWithAI(message: string): Promise<ChatResult> {
  return request<ChatResult>("/api/ai/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}
