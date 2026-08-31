import { expect, test } from "@playwright/test";

const api = process.env.VITE_API_URL ?? "http://localhost:8000/api/v1";
let cameraId: number | undefined;

test.afterEach(async ({ request }) => {
  if (cameraId) await request.delete(`${api}/cameras/${cameraId}`);
  cameraId = undefined;
});

test("cadastra, edita e exibe a URL RTMP de uma câmera", async ({ page }) => {
  await page.goto("/cameras");
  await page.getByRole("button", { name: "Nova câmera" }).click();
  await page.getByLabel("Nome").fill("E2E Entrada");
  await page.getByLabel("Localização").fill("Recepção");
  await page.getByRole("button", { name: "Cadastrar câmera" }).click();
  await expect(page.getByText("Credenciais de publicação")).toBeVisible();
  const rtmp = page.locator("code");
  await expect(rtmp).toContainText("rtmp://");
  await page.getByRole("button", { name: "Fechar" }).click();
  await page.getByTitle("Editar").click();
  await page.getByLabel("Nome").fill("E2E Portão");
  await page.getByRole("button", { name: "Salvar alterações" }).click();
  await expect(page.getByText("E2E Portão")).toBeVisible();
  const response = await page.request.get(`${api}/cameras?include_disabled=true`);
  const cameras = await response.json();
  cameraId = cameras.find((camera: { name: string }) => camera.name === "E2E Portão")?.id;
});

test("desabilita e exclui uma câmera pelo painel", async ({ page }) => {
  await page.goto("/cameras");
  await page.getByRole("button", { name: "Nova câmera" }).click();
  await page.getByLabel("Nome").fill("E2E Desativação");
  await page.getByRole("button", { name: "Cadastrar câmera" }).click();
  await page.getByRole("button", { name: "Fechar" }).click();

  const row = page.getByRole("row", { name: /E2E Desativação/ });
  await row.getByTitle("Editar").click();
  await page.getByLabel("Câmera habilitada para publicação e monitoramento").uncheck();
  await page.getByRole("button", { name: "Salvar alterações" }).click();
  await expect(row.getByText("Desabilitada")).toBeVisible();

  page.once("dialog", (dialog) => dialog.accept());
  await row.getByTitle("Excluir").click();
  await expect(page.getByRole("row", { name: /E2E Desativação/ })).toHaveCount(0);
});

test("registra um evento com horário informado e abre seus detalhes", async ({ page, request }) => {
  const createResponse = await request.post(`${api}/cameras`, {
    data: { name: "E2E Eventos", pre_alarm_seconds: 0, post_alarm_seconds: 1 },
  });
  cameraId = (await createResponse.json()).id;
  const happenedAt = new Date(Date.now() - 30_000).toISOString().slice(0, 16);

  await page.goto("/events");
  await page.getByLabel("Filtrar câmera").selectOption({ label: "E2E Eventos" });
  await page.getByRole("button", { name: "Registrar evento" }).click();
  await page.getByLabel("Tipo").fill("E2E Movimento");
  await page.getByLabel(/Data e hora da ocorrência/).fill(happenedAt);
  await page.getByRole("button", { name: "Registrar" }).click();
  await expect(page.getByText("E2E Movimento")).toBeVisible();
  await page.getByTitle("Ver detalhes").click();
  await expect(page.getByText("Detalhes do evento")).toBeVisible();
});

test("bloqueia visualmente um período de histórico inválido", async ({ page }) => {
  await page.goto("/history");
  await page.getByLabel("Início").fill("2030-01-01T12:00");
  await page.getByLabel("Fim").fill("2030-01-01T11:00");
  await expect(page.getByText("O início deve ser anterior ao fim.")).toBeVisible();
});
