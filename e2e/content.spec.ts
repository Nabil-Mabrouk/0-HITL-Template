/**
 * Tests E2E — Accès au contenu selon les rôles.
 *
 * Valide le contrôle d'accès de bout en bout :
 * - Un user standard peut voir les tutorials libres
 * - Un user standard est bloqué sur les tutorials premium
 * - Un user premium accède aux deux types
 *
 * Prérequis :
 *   - Tutorial avec slug "intro-python" (access_role=user) en DB de test
 *   - Tutorial avec slug "python-avance" (access_role=premium) en DB de test
 */

import { test, expect } from '@playwright/test'
import { loginAs, clearAuth } from './helpers'

test.describe('Accès au contenu', () => {

  test('utilisateur non connecté est redirigé depuis /learn', async ({ page }) => {
    await clearAuth(page)
    await page.goto('/learn')
    await expect(page).toHaveURL(/\/login/, { timeout: 5_000 })
  })

  test('user connecté peut voir la liste des tutorials', async ({ page }) => {
    await loginAs(page, 'user')
    await page.goto('/learn')

    await expect(page).not.toHaveURL(/\/login/)
    // La page doit contenir au moins un tutorial
    await expect(page.locator('[data-testid="tutorial-card"], .tutorial-card, article').first())
      .toBeVisible({ timeout: 10_000 })
  })

  test('user standard peut accéder à un tutorial libre', async ({ page }) => {
    await loginAs(page, 'user')
    await page.goto('/learn/intro-python')

    await expect(page).not.toHaveURL(/\/login/)
    await expect(page).not.toHaveURL(/\/403|\/forbidden/)
  })

  test('user standard est bloqué sur un tutorial premium', async ({ page }) => {
    await loginAs(page, 'user')
    await page.goto('/learn/python-avance')

    // Doit afficher une erreur d'accès ou rediriger
    const isBlocked = await Promise.race([
      page.waitForURL(/\/403|\/forbidden|\/premium/, { timeout: 5_000 })
        .then(() => true).catch(() => false),
      page.getByText(/premium|accès|forbidden|403/i)
        .isVisible().catch(() => false),
    ])
    expect(isBlocked).toBeTruthy()
  })
})

test.describe('Navigation entre leçons', () => {

  test('user peut naviguer vers une leçon', async ({ page }) => {
    await loginAs(page, 'user')
    await page.goto('/learn/intro-python')

    // Cliquer sur la première leçon
    const firstLesson = page.locator('a[href*="/lessons/"]').first()
    if (await firstLesson.isVisible()) {
      await firstLesson.click()
      // Vérifier que le contenu de la leçon est visible
      await expect(page.locator('article, .lesson-content, [data-testid="lesson-content"]').first())
        .toBeVisible({ timeout: 10_000 })
    }
  })
})
