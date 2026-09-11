import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BoardApp } from "./BoardApp";
import * as api from "@/lib/api";
import { seedBoard } from "@/lib/seedData";

vi.mock("@/lib/api");

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function mockFetchBoard() {
  vi.mocked(api.fetchBoard).mockResolvedValue(seedBoard);
}

describe("BoardApp", () => {
  it("shows a loading state before the board loads", async () => {
    let resolveBoard: (board: typeof seedBoard) => void = () => {};
    vi.mocked(api.fetchBoard).mockReturnValue(
      new Promise((resolve) => {
        resolveBoard = resolve;
      })
    );
    render(<BoardApp onLogout={() => {}} />);

    expect(screen.getByText("Cargando tablero…")).toBeInTheDocument();

    resolveBoard(seedBoard);
    expect(await screen.findByRole("button", { name: "Backlog" })).toBeInTheDocument();
  });

  it("loads and renders the board from the API", async () => {
    mockFetchBoard();
    render(<BoardApp onLogout={() => {}} />);

    expect(screen.getByRole("heading", { name: "Curso Claude" })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Backlog" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Por hacer" })).toBeInTheDocument();
    expect(screen.getByText("Definir arquitectura del backend")).toBeInTheDocument();
  });

  it("shows an error message when the board fails to load", async () => {
    vi.mocked(api.fetchBoard).mockRejectedValue(new Error("network"));
    render(<BoardApp onLogout={() => {}} />);

    expect(await screen.findByText("No se ha podido cargar el tablero.")).toBeInTheDocument();
  });

  it("adds a new card via the API", async () => {
    mockFetchBoard();
    const updatedBoard = {
      ...seedBoard,
      columns: seedBoard.columns.map((column) =>
        column.id === "backlog" ? { ...column, cardIds: [...column.cardIds, "new-card"] } : column
      ),
      cards: {
        ...seedBoard.cards,
        "new-card": { id: "new-card", title: "Tarjeta de prueba", details: "Detalles de prueba" },
      },
    };
    vi.mocked(api.createCard).mockResolvedValue(updatedBoard);

    const user = userEvent.setup();
    render(<BoardApp onLogout={() => {}} />);
    await screen.findByRole("button", { name: "Backlog" });

    await user.click(screen.getAllByText("+ Añadir tarjeta")[0]);
    await user.type(screen.getByPlaceholderText("Título de la tarjeta"), "Tarjeta de prueba");
    await user.type(screen.getByPlaceholderText("Detalles"), "Detalles de prueba");
    await user.click(screen.getByRole("button", { name: "Añadir" }));

    expect(api.createCard).toHaveBeenCalledWith("backlog", "Tarjeta de prueba", "Detalles de prueba");
    expect(await screen.findByText("Tarjeta de prueba")).toBeInTheDocument();
  });

  it("does not call the API when the title is empty", async () => {
    mockFetchBoard();
    const user = userEvent.setup();
    render(<BoardApp onLogout={() => {}} />);
    await screen.findByRole("button", { name: "Backlog" });

    await user.click(screen.getAllByText("+ Añadir tarjeta")[0]);
    await user.click(screen.getByRole("button", { name: "Añadir" }));

    expect(api.createCard).not.toHaveBeenCalled();
    expect(screen.getByPlaceholderText("Título de la tarjeta")).toBeInTheDocument();
  });

  it("edits a card via the API", async () => {
    mockFetchBoard();
    const updatedBoard = {
      ...seedBoard,
      cards: {
        ...seedBoard.cards,
        "card-1": { id: "card-1", title: "Título editado", details: "Detalles editados" },
      },
    };
    vi.mocked(api.updateCard).mockResolvedValue(updatedBoard);

    const user = userEvent.setup();
    render(<BoardApp onLogout={() => {}} />);
    await screen.findByText("Definir arquitectura del backend");

    await user.click(screen.getByRole("button", { name: "Editar tarjeta Definir arquitectura del backend" }));
    const titleInput = screen.getByLabelText("Título de Definir arquitectura del backend");
    await user.clear(titleInput);
    await user.type(titleInput, "Título editado");
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(api.updateCard).toHaveBeenCalledWith(
      "card-1",
      "Título editado",
      "Evaluar si conviene una API REST o GraphQL y documentar la decisión."
    );
    expect(await screen.findByText("Título editado")).toBeInTheDocument();
  });

  it("cancels a card edit without calling the API", async () => {
    mockFetchBoard();
    const user = userEvent.setup();
    render(<BoardApp onLogout={() => {}} />);
    await screen.findByText("Definir arquitectura del backend");

    await user.click(screen.getByRole("button", { name: "Editar tarjeta Definir arquitectura del backend" }));
    const titleInput = screen.getByLabelText("Título de Definir arquitectura del backend");
    await user.clear(titleInput);
    await user.type(titleInput, "Algo distinto");
    await user.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(api.updateCard).not.toHaveBeenCalled();
    expect(screen.getByText("Definir arquitectura del backend")).toBeInTheDocument();
  });

  it("deletes a card via the API", async () => {
    mockFetchBoard();
    const updatedBoard = {
      columns: seedBoard.columns.map((column) =>
        column.id === "backlog" ? { ...column, cardIds: column.cardIds.filter((id) => id !== "card-1") } : column
      ),
      cards: Object.fromEntries(Object.entries(seedBoard.cards).filter(([id]) => id !== "card-1")),
    };
    vi.mocked(api.deleteCard).mockResolvedValue(updatedBoard);

    const user = userEvent.setup();
    render(<BoardApp onLogout={() => {}} />);
    await screen.findByText("Definir arquitectura del backend");

    await user.click(screen.getByRole("button", { name: /Eliminar tarjeta Definir arquitectura del backend/ }));

    expect(api.deleteCard).toHaveBeenCalledWith("card-1");
    expect(await screen.findByText("Investigar proveedores de hosting")).toBeInTheDocument();
    expect(screen.queryByText("Definir arquitectura del backend")).not.toBeInTheDocument();
  });

  it("renames a column via the API", async () => {
    mockFetchBoard();
    const updatedBoard = {
      ...seedBoard,
      columns: seedBoard.columns.map((column) =>
        column.id === "backlog" ? { ...column, name: "Ideas" } : column
      ),
    };
    vi.mocked(api.renameColumn).mockResolvedValue(updatedBoard);

    const user = userEvent.setup();
    render(<BoardApp onLogout={() => {}} />);
    await screen.findByRole("button", { name: "Backlog" });

    await user.click(screen.getByRole("button", { name: "Backlog" }));
    const input = screen.getByLabelText("Nombre de la columna");
    await user.clear(input);
    await user.type(input, "Ideas{Enter}");

    expect(api.renameColumn).toHaveBeenCalledWith("backlog", "Ideas");
    expect(await screen.findByRole("button", { name: "Ideas" })).toBeInTheDocument();
  });

  it("cancels a column rename with Escape without calling the API", async () => {
    mockFetchBoard();
    const user = userEvent.setup();
    render(<BoardApp onLogout={() => {}} />);
    await screen.findByRole("button", { name: "Backlog" });

    await user.click(screen.getByRole("button", { name: "Backlog" }));
    const input = screen.getByLabelText("Nombre de la columna");
    await user.clear(input);
    await user.type(input, "Algo distinto{Escape}");

    expect(api.renameColumn).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Backlog" })).toBeInTheDocument();
  });

  it("logs out and calls onLogout", async () => {
    mockFetchBoard();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 200 })));
    const onLogout = vi.fn();
    const user = userEvent.setup();
    render(<BoardApp onLogout={onLogout} />);
    await screen.findByRole("button", { name: "Backlog" });

    await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));

    expect(fetch).toHaveBeenCalledWith("/api/logout", expect.objectContaining({ method: "POST" }));
    expect(onLogout).toHaveBeenCalled();
  });
});
