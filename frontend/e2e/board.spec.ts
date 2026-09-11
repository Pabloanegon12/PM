import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Usuario").fill("user");
  await page.getByLabel("Contraseña").fill("password");
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("heading", { name: "Curso Claude" })).toBeVisible();
});

test("requires login to see the board", async ({ page }) => {
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible();

  await page.reload();
  await expect(page.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible();
});

test("adding a card persists after reloading the page", async ({ page }) => {
  const title = `Tarjeta e2e ${Date.now()}`;

  await page.getByText("+ Añadir tarjeta").first().click();
  await page.getByPlaceholder("Título de la tarjeta").fill(title);
  await page.getByPlaceholder("Detalles").fill("Creada por Playwright");
  await page.getByRole("button", { name: "Añadir", exact: true }).click();
  await expect(page.getByText(title, { exact: true })).toBeVisible();

  await page.reload();

  await expect(page.getByRole("heading", { name: "Curso Claude" })).toBeVisible();
  await expect(page.getByText(title, { exact: true })).toBeVisible();
});

test("deleting a card persists after reloading the page", async ({ page }) => {
  const title = `Tarjeta a borrar ${Date.now()}`;

  await page.getByText("+ Añadir tarjeta").first().click();
  await page.getByPlaceholder("Título de la tarjeta").fill(title);
  await page.getByRole("button", { name: "Añadir", exact: true }).click();
  const card = page.getByText(title, { exact: true });
  await expect(card).toBeVisible();

  await card.hover();
  await page.getByRole("button", { name: `Eliminar tarjeta ${title}`, exact: true }).click();
  await expect(card).not.toBeVisible();

  await page.reload();
  await expect(page.getByText(title, { exact: true })).not.toBeVisible();
});

test("editing a card persists after reloading the page", async ({ page }) => {
  const title = `Tarjeta a editar ${Date.now()}`;
  const editedTitle = `${title} (editada)`;

  await page.getByText("+ Añadir tarjeta").first().click();
  await page.getByPlaceholder("Título de la tarjeta").fill(title);
  await page.getByRole("button", { name: "Añadir", exact: true }).click();
  const card = page.getByText(title, { exact: true });
  await expect(card).toBeVisible();

  await card.hover();
  await page.getByRole("button", { name: `Editar tarjeta ${title}`, exact: true }).click();
  const titleInput = page.getByLabel(`Título de ${title}`);
  await titleInput.fill(editedTitle);
  await page.getByRole("button", { name: "Guardar", exact: true }).click();

  await expect(page.getByText(editedTitle, { exact: true })).toBeVisible();

  await page.reload();
  await expect(page.getByText(editedTitle, { exact: true })).toBeVisible();

  // cleanup
  const editedCard = page.getByText(editedTitle, { exact: true });
  await editedCard.hover();
  await page.getByRole("button", { name: `Eliminar tarjeta ${editedTitle}`, exact: true }).click();
  await expect(editedCard).not.toBeVisible();
});

test("renaming a column persists after reloading the page", async ({ page }) => {
  const temporaryName = `Ideas e2e ${Date.now()}`;

  await page.getByRole("button", { name: "Backlog" }).click();
  const input = page.getByLabel("Nombre de la columna");
  await input.fill(temporaryName);
  await input.press("Enter");
  await expect(page.getByRole("button", { name: temporaryName })).toBeVisible();

  await page.reload();
  await expect(page.getByRole("button", { name: temporaryName })).toBeVisible();

  await page.getByRole("button", { name: temporaryName }).click();
  const revertInput = page.getByLabel("Nombre de la columna");
  await revertInput.fill("Backlog");
  await revertInput.press("Enter");
  await expect(page.getByRole("button", { name: "Backlog" })).toBeVisible();
});

test("dragging a card to another column persists after reloading the page", async ({ page }) => {
  const title = `Tarjeta drag ${Date.now()}`;

  await page.getByText("+ Añadir tarjeta").first().click();
  await page.getByPlaceholder("Título de la tarjeta").fill(title);
  await page.getByRole("button", { name: "Añadir", exact: true }).click();
  const card = page.getByText(title, { exact: true });
  await expect(card).toBeVisible();

  const target = page.getByText("Configurar repositorio en GitHub");
  const cardBox = await card.boundingBox();
  const targetBox = await target.boundingBox();
  if (!cardBox || !targetBox) throw new Error("Could not measure drag source/target");

  await page.mouse.move(cardBox.x + cardBox.width / 2, cardBox.y + cardBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(cardBox.x + cardBox.width / 2 + 10, cardBox.y + cardBox.height / 2, { steps: 5 });
  await page.mouse.move(targetBox.x + targetBox.width / 2, targetBox.y + targetBox.height / 2, { steps: 10 });

  // Wait for the move to actually reach the backend before reloading — the drop
  // updates the UI optimistically first, and reloading too early would abort
  // the in-flight request and lose the move.
  const [moveResponse] = await Promise.all([
    page.waitForResponse((response) => /\/api\/board\/cards\/.+\/move$/.test(response.url())),
    page.mouse.up(),
  ]);
  expect(moveResponse.ok()).toBeTruthy();

  const hechoColumn = page.getByRole("button", { name: "Hecho" }).locator("..").locator("..");
  await expect(hechoColumn.getByText(title, { exact: true })).toBeVisible();

  await page.reload();

  const hechoColumnAfterReload = page.getByRole("button", { name: "Hecho" }).locator("..").locator("..");
  await expect(hechoColumnAfterReload.getByText(title, { exact: true })).toBeVisible();

  await hechoColumnAfterReload.getByText(title, { exact: true }).hover();
  await page.getByRole("button", { name: `Eliminar tarjeta ${title}`, exact: true }).click();
  await expect(page.getByText(title, { exact: true })).not.toBeVisible();
});
