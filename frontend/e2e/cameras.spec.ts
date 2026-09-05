import { expect, test, type Page } from "@playwright/test";

const admin = {
  id: 1,
  email: "admin@malupe.com",
  full_name: "Administrador",
  is_active: true,
  created_at: new Date().toISOString(),
  last_login_at: null,
  roles: ["Administrador"],
  permissions: [
    "overview.read",
    "reports.read",
    "mosaics.read",
    "mosaics.manage",
    "cameras.read",
    "cameras.manage",
    "events.read",
    "events.manage",
    "users.manage",
    "permissions.manage",
    "system.health.read",
  ],
};
async function mockApi(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const json = (body: unknown, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (path.endsWith("/auth/refresh"))
      return json({ access_token: "token", token_type: "bearer", expires_in: 900, user: admin });
    if (path.endsWith("/auth/me")) return json(admin);
    if (path.endsWith("/camera-status/summary"))
      return json({ online: 5, unstable: 1, offline: 2, total: 8, generated_at: new Date().toISOString() });
    if (path.endsWith("/camera-status/history")) return json([]);
    if (path.endsWith("/health"))
      return json({
        ok: true,
        database: "up",
        mediamtx: "up",
        active_streams: 5,
        version: "0.5.0",
        effective_retention_hours: 1,
      });
    if (path.endsWith("/users")) return json([{ ...admin, updated_at: new Date().toISOString() }]);
    if (path.endsWith("/roles"))
      return json([
        {
          id: 1,
          name: "Administrador",
          description: "Perfil",
          permission_codes: admin.permissions,
          is_system: true,
          user_count: 1,
          created_at: new Date().toISOString(),
        },
      ]);
    if (path.endsWith("/cameras"))
      return json([
        {
          id: 1,
          name: "Portaria",
          location: "Entrada",
          audio_enabled: true,
          pre_alarm_seconds: 30,
          post_alarm_seconds: 60,
          enabled: true,
          created_at: new Date().toISOString(),
          status: "online",
          hls_url: "",
          effective_retention_hours: 1,
        },
      ]);
    if (path.endsWith("/mosaics") && route.request().method() === "POST")
      return json(
        {
          id: 10,
          name: "Portaria",
          capacity: 4,
          columns: 2,
          rows: 2,
          active: true,
          camera_count: 1,
          user_count: 1,
          cameras: [],
          user_ids: [1],
          role_ids: [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        201,
      );
    if (path.endsWith("/mosaics")) return json([]);
    return json({ detail: "Não encontrado" }, 404);
  });
}

test("protege a central quando não existe refresh válido", async ({ page }) => {
  await page.route("**/api/v1/auth/refresh", (route) =>
    route.fulfill({
      status: 401,
      contentType: "application/json",
      body: '{"detail":"Refresh token ausente"}',
    }),
  );
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Entrar na central" })).toBeVisible();
});

test("mostra somente conectividade na visão geral", async ({ page }) => {
  await mockApi(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Visão geral" })).toBeVisible();
  await expect(page.getByText("5", { exact: true })).toBeVisible();
  await expect(page.getByText("1", { exact: true })).toBeVisible();
  await expect(page.getByText("2", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Histórico de conectividade" })).toBeVisible();
});

test("cria mosaico pelo wizard de 3 etapas", async ({ page }) => {
  await mockApi(page);
  await page.goto("/mosaics/new");
  await page.getByLabel("Nome do mosaico").fill("Portaria");
  await page.getByRole("button", { name: /Avançar/ }).click();
  await page.getByRole("button", { name: "Adicionar Administrador" }).click();
  await page.getByRole("button", { name: /Avançar/ }).click();
  await page.getByRole("button", { name: "Adicionar Portaria" }).click();
  await page.getByRole("button", { name: "Criar mosaico" }).click();
  await expect(page).toHaveURL(/\/mosaics\/10$/);
});
