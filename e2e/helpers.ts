/**
 * Helpers partagés pour les tests E2E Playwright.
 *
 * Fournit :
 * - loginAs() : connexion via l'API + stockage du token
 * - clearAuth() : effacement des données d'authentification
 * - waitForToast() : attente d'un message de notification
 */

import { Page, expect } from '@playwright/test'

const API_URL = process.env.PLAYWRIGHT_API_URL ?? 'http://localhost:8000'

// ── Utilisateurs de test (doivent exister en DB de test) ─────────────────────

export const TEST_USERS = {
  admin: {
    email: 'admin@test.com',
    password: 'AdminTest123!',
  },
  user: {
    email: 'e2euser@test.com',
    password: 'Password123!',
  },
  premium: {
    email: 'e2epremium@test.com',
    password: 'Password123!',
  },
}

// ── Helpers d'authentification ────────────────────────────────────────────────

/**
 * Connecte un utilisateur via l'API et stocke le token dans localStorage.
 * Plus rapide que de passer par le formulaire de connexion dans chaque test.
 */
export async function loginAs(
  page: Page,
  role: keyof typeof TEST_USERS = 'user',
): Promise<void> {
  const credentials = TEST_USERS[role]

  // Appel API direct (bypass UI)
  const response = await page.request.post(`${API_URL}/api/auth/login`, {
    data: credentials,
  })

  if (!response.ok()) {
    throw new Error(
      `loginAs(${role}) failed: ${response.status()} — ` +
      `Ensure test user ${credentials.email} exists in the test DB`
    )
  }

  const { access_token } = await response.json()

  // Injecter le token dans localStorage (sans passer par l'UI)
  await page.goto('/')
  await page.evaluate(
    (token: string) => localStorage.setItem('access_token', token),
    access_token,
  )
}

/**
 * Efface toutes les données d'authentification.
 */
export async function clearAuth(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  })
}

// ── Helpers de navigation ─────────────────────────────────────────────────────

/**
 * Navigue vers une page et attend qu'elle soit chargée.
 */
export async function navigateTo(page: Page, path: string): Promise<void> {
  await page.goto(path)
  await page.waitForLoadState('networkidle')
}

/**
 * Attend qu'un message toast/notification apparaisse.
 */
export async function waitForToast(
  page: Page,
  text: string | RegExp,
): Promise<void> {
  await expect(
    page.locator('[role="alert"], .toast, [data-toast]').filter({ hasText: text })
  ).toBeVisible({ timeout: 5_000 })
}
