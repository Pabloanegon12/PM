import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatSidebar } from "./ChatSidebar";
import * as api from "@/lib/api";
import { seedBoard } from "@/lib/seedData";

vi.mock("@/lib/api");

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ChatSidebar", () => {
  it("sends a message, shows the AI response and updates the board", async () => {
    let resolveChat: (value: { message: string; board: typeof seedBoard }) => void = () => {};
    vi.mocked(api.chatWithAI).mockReturnValue(
      new Promise((resolve) => {
        resolveChat = resolve;
      })
    );
    const onBoardUpdate = vi.fn();
    const user = userEvent.setup();
    render(<ChatSidebar onBoardUpdate={onBoardUpdate} />);

    await user.type(screen.getByPlaceholderText("Escribe un mensaje…"), "hola");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(screen.getByText("hola")).toBeInTheDocument();
    expect(screen.getByText("IA escribiendo…")).toBeInTheDocument();
    expect(api.chatWithAI).toHaveBeenCalledWith("hola");

    resolveChat({ message: "¡Hola! ¿En qué puedo ayudarte?", board: seedBoard });

    expect(await screen.findByText("¡Hola! ¿En qué puedo ayudarte?")).toBeInTheDocument();
    expect(onBoardUpdate).toHaveBeenCalledWith(seedBoard);
    expect(screen.queryByText("IA escribiendo…")).not.toBeInTheDocument();
  });

  it("does not send an empty message", async () => {
    const user = userEvent.setup();
    render(<ChatSidebar onBoardUpdate={() => {}} />);

    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(api.chatWithAI).not.toHaveBeenCalled();
  });

  it("shows an error message when the request fails", async () => {
    vi.mocked(api.chatWithAI).mockRejectedValue(new Error("network"));
    const user = userEvent.setup();
    render(<ChatSidebar onBoardUpdate={() => {}} />);

    await user.type(screen.getByPlaceholderText("Escribe un mensaje…"), "hola");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByText("No se ha podido contactar con la IA.")).toBeInTheDocument();
  });
});
