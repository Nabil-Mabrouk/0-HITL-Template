import { defineConfig, devices } from "@playwright/test";

/**
 * Configuration Playwright pour les tests E2E.
 *
 * Les tests E2E nécessitent que le frontend et le backend soient lancés.
 * En CI, utiliser les webServers pour démarrer automatiquement.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
  ],

  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Démarrage automatique en développement local
  // webServer: [
  //   {
  //     command: "cd backend && uvicorn app.main:app --port 8000",
  //     port: 8000,
  //     reuseExistingServer: !process.env.CI,
  //   },
  //   {
  //     command: "cd frontend && npm run dev",
  //     port: 5173,
  //     reuseExistingServer: !process.env.CI,
  //   },
  // ],
});
