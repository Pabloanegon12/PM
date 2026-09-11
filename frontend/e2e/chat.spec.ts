import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Usuario").fill("user");
  await page.getByLabel("Contraseña").fill("password");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("heading", { name: "Curso Claude" })).toBeVisible();
});

// This test talks to the real OpenRouter model (a reasoning model), which
// regularly takes 30-90s to answer (sometimes much longer), so it needs a
// much longer timeout than the rest of the suite. The backend itself gives
// up on the AI call after 200s (app/ai.py), so this test's patience must
// exceed that.
test("chatting with the AI can create a card and refresh the board", async ({ page }) => {
  test.setTimeout(230_000);

  const title = `Tarjeta e2e chat ${Date.now()}`;

  await page
    .getByPlaceholder("Escribe un mensaje…")
    .fill(
      `Crea una tarjeta en la columna Backlog con el titulo exacto "${title}" y sin detalles. No hagas ningun otro cambio.`
    );
  await page.getByRole("button", { name: "Enviar" }).click();

  await expect(page.getByText("IA escribiendo…")).toBeVisible();
  await expect(page.getByText("IA escribiendo…")).not.toBeVisible({ timeout: 210_000 });

  await expect(page.getByText(title, { exact: true })).toBeVisible();

  // cleanup
  const card = page.getByText(title, { exact: true });
  await card.hover();
  await page.getByRole("button", { name: `Eliminar tarjeta ${title}`, exact: true }).click();
  await expect(card).not.toBeVisible();
});
