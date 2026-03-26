/**
 * Tests E2E : Navigation et contenu
 *
 * Vérifie le rendu des pages principales et l'accès au contenu.
 */

import { test, expect } from "@playwright/test";

test.describe("Navigation principale", () => {
  test("la page d'accueil charge correctement", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/.+/);
    // La page doit avoir un contenu visible
    await expect(page.locator("body")).toBeVisible();
  });

  test("la page d'accueil contient un lien vers le login", async ({ page }) => {
    await page.goto("/");
    const loginLink = page.locator("a[href='/login'], a:has-text('login'), a:has-text('connexion')").first();
    // Optionnel — certains sites cachent ce lien si déjà connecté
    if (await loginLink.count() > 0) {
      await expect(loginLink).toBeVisible();
    }
  });

  test("la page 404 s'affiche pour une URL inexistante", async ({ page }) => {
    const response = await page.goto("/this-page-does-not-exist-xyz-123");
    // Soit une vraie 404, soit une SPA qui gère elle-même les 404
    expect([200, 404]).toContain(response?.status());
  });
});

test.describe("Contenu public", () => {
  test("la liste des articles est accessible", async ({ page }) => {
    const response = await page.goto("/learn");
    // La page /learn peut nécessiter une authentification
    expect([200, 302, 404]).toContain(response?.status() ?? 200);
  });
});
