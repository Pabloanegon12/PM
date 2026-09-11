import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AuthGate } from "./AuthGate";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("AuthGate", () => {
  it("shows the login form when there is no active session", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 401 }))
    );
    render(<AuthGate />);

    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
  });

  it("shows the board when there is an active session", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 200 }))
    );
    render(<AuthGate />);

    expect(await screen.findByRole("heading", { name: "Curso Claude" })).toBeInTheDocument();
  });
});
