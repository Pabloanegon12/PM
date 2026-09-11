import { describe, expect, it } from "vitest";
import { moveCardInBoard } from "./boardDrag";
import { seedBoard } from "./seedData";
import type { Board } from "./types";

describe("seedBoard", () => {
  it("has exactly 5 columns with the expected names", () => {
    expect(seedBoard.columns).toHaveLength(5);
    expect(seedBoard.columns.map((column) => column.name)).toEqual([
      "Backlog",
      "Por hacer",
      "En curso",
      "En revisión",
      "Hecho",
    ]);
  });

  it("has a card entry for every id referenced by a column", () => {
    for (const column of seedBoard.columns) {
      for (const cardId of column.cardIds) {
        expect(seedBoard.cards[cardId]).toBeDefined();
      }
    }
  });
});

describe("moveCardInBoard", () => {
  it("moves a card from one column to another at the given index", () => {
    const next = moveCardInBoard(seedBoard, {
      cardId: "card-1",
      fromColumnId: "backlog",
      toColumnId: "done",
      toIndex: 0,
    });

    expect(next.columns.find((c) => c.id === "backlog")?.cardIds).not.toContain("card-1");
    expect(next.columns.find((c) => c.id === "done")?.cardIds[0]).toBe("card-1");
  });

  it("reorders a card within the same column", () => {
    const board: Board = {
      ...seedBoard,
      columns: seedBoard.columns.map((column) =>
        column.id === "backlog" ? { ...column, cardIds: ["card-1", "card-2"] } : column
      ),
    };

    const next = moveCardInBoard(board, {
      cardId: "card-1",
      fromColumnId: "backlog",
      toColumnId: "backlog",
      toIndex: 1,
    });

    expect(next.columns.find((c) => c.id === "backlog")?.cardIds).toEqual(["card-2", "card-1"]);
  });
});
