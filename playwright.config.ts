import { defineConfig, devices } from '@playwright/test'

/**
 * Configuration Playwright pour les tests E2E de Z-HITL.
 *
 * Les tests E2E nécessitent que les services soient démarrés :
 *   docker-compose -f docker-compose.dev.yml up -d
 *
 * Ou via les webServer ci-dessous (démarrage automatique).
 *
 * Docs : https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Répertoire des tests E2E
  testDir: './e2e',

  // Timeout global par test (30 secondes)
  timeout: 30_000,

  // Timeout pour les assertions (5 secondes)
  expect: {
    timeout: 5_000,
  },

  // Nombre de retentatives en CI
  retries: process.env.CI ? 2 : 0,

  // Workers parallèles
  workers: process.env.CI ? 1 : undefined,

  // Rapport de test
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ...(process.env.CI ? [['github'] as ['github']] : []),
  ],

  use: {
    // URL de base de l'application
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5173',

    // Captures automatiques en cas d'échec
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
  },

  projects: [
    // ── Navigateurs de test ──────────────────────────────────────────────────
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
    },
  ],

  // ── Démarrage automatique du frontend en développement ────────────────────
  // Décommentez pour démarrer Vite automatiquement avant les tests
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:5173',
  //   cwd: './frontend',
  //   reuseExistingServer: !process.env.CI,
  // },
})
