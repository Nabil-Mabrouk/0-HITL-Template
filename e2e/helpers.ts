/**
 * Helpers partagés pour les tests E2E Playwright.
 *
 * Fournit des fonctions utilitaires pour l'authentification,
 * la navigation et les assertions courantes.
 */

import { Page, expect } from "@playwright/test";

const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000";

/**
 * Authentifie un utilisateur via l'API directement (bypass UI).
 * Plus rapide et plus fiable que passer par le formulaire de login.
 */
export async function loginAs(
  page: Page,
  email: string,
  password: string
): Promise<void> {
  const response = await page.request.post(`${API_URL}/auth/login`, {
    data: { email, password },
  });

  if (!response.ok()) {
    throw new Error(`Login failed: ${response.status()} - ${await response.text()}`);
  }

  const { access_token } = await response.json();
  await page.evaluate((token) => {
    localStorage.setItem("access_token", token);
  }, access_token);
}

/**
 * Attend que la page soit complètement chargée.
 */
export async function waitForPageLoad(page: Page): Promise<void> {
  await page.waitForLoadState("networkidle");
}

/**
 * Vérifie qu'une notification toast est affichée.
 */
export async function expectToast(page: Page, text: string | RegExp): Promise<void> {
  await expect(page.locator("[role='alert'], .toast, [data-toast]").first()).toContainText(text);
}
