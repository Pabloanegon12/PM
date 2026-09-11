import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LoginForm } from "./LoginForm";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("LoginForm", () => {
  it("calls onSuccess when the credentials are correct", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 200 }))
    );
    const onSuccess = vi.fn();
    const user = userEvent.setup();
    render(<LoginForm onSuccess={onSuccess} />);

    await user.type(screen.getByLabelText("Usuario"), "user");
    await user.type(screen.getByLabelText("Contraseña"), "password");
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(onSuccess).toHaveBeenCalled();
  });

  it("shows an error when the credentials are incorrect", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 401 }))
    );
    const onSuccess = vi.fn();
    const user = userEvent.setup();
    render(<LoginForm onSuccess={onSuccess} />);

    await user.type(screen.getByLabelText("Usuario"), "user");
    await user.type(screen.getByLabelText("Contraseña"), "incorrecta");
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(screen.getByText("Usuario o contraseña incorrectos.")).toBeInTheDocument();
    expect(onSuccess).not.toHaveBeenCalled();
  });
});
