/**
 * Tests E2E — Flux d'authentification complets.
 *
 * Couvre les parcours utilisateur de bout en bout :
 * - Connexion réussie et redirection
 * - Connexion échouée avec message d'erreur
 * - Déconnexion
 * - Accès refusé aux pages protégées
 * - Redirection après connexion
 *
 * Prérequis :
 *   - Application frontend sur http://localhost:5173
 *   - API backend sur http://localhost:8000
 *   - Utilisateur e2euser@test.com / Password123! en DB de test
 */

import { test, expect } from '@playwright/test'
import { loginAs, clearAuth, TEST_USERS } from './helpers'

// ── Connexion ─────────────────────────────────────────────────────────────────

test.describe('Connexion (Login)', () => {

  test.beforeEach(async ({ page }) => {
    await clearAuth(page)
  })

  test('formulaire de connexion visible', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByPlaceholder(/email/i)).toBeVisible()
    await expect(page.getByPlaceholder(/password|mot de passe/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /connexion|login|se connecter/i })).toBeVisible()
  })

  test('connexion réussie redirige vers /profile', async ({ page }) => {
    await page.goto('/login')

    await page.getByPlaceholder(/email/i).fill(TEST_USERS.user.email)
    await page.getByPlaceholder(/password|mot de passe/i).fill(TEST_USERS.user.password)
    await page.getByRole('button', { name: /connexion|login|se connecter/i }).click()

    // Attendre la redirection vers le profil
    await expect(page).toHaveURL(/\/profile/, { timeout: 10_000 })
  })

  test('mauvais mot de passe affiche une erreur', async ({ page }) => {
    await page.goto('/login')

    await page.getByPlaceholder(/email/i).fill(TEST_USERS.user.email)
    await page.getByPlaceholder(/password|mot de passe/i).fill('WrongPassword!')
    await page.getByRole('button', { name: /connexion|login|se connecter/i }).click()

    // Le message d'erreur doit apparaître
    await expect(page.getByText(/invalide|incorrect|erreur/i)).toBeVisible({ timeout: 5_000 })

    // Rester sur la page de login
    await expect(page).toHaveURL(/\/login/)
  })

  test('email inconnu ne révèle pas l\'existence du compte', async ({ page }) => {
    await page.goto('/login')

    await page.getByPlaceholder(/email/i).fill('nobody@nowhere.com')
    await page.getByPlaceholder(/password|mot de passe/i).fill('SomePassword123!')
    await page.getByRole('button', { name: /connexion|login|se connecter/i }).click()

    // Doit afficher une erreur générique (pas "utilisateur non trouvé")
    await expect(page.getByText(/invalide|incorrect|erreur/i)).toBeVisible({ timeout: 5_000 })
  })
})

// ── Pages protégées ───────────────────────────────────────────────────────────

test.describe('Protection des routes', () => {

  test.beforeEach(async ({ page }) => {
    await clearAuth(page)
  })

  test('/profile redirige vers /login si non connecté', async ({ page }) => {
    await page.goto('/profile')
    // Attendre la redirection
    await expect(page).toHaveURL(/\/login/, { timeout: 5_000 })
  })

  test('page accessible après connexion', async ({ page }) => {
    await loginAs(page, 'user')
    await page.goto('/profile')
    // Ne doit pas rediriger vers login
    await expect(page).not.toHaveURL(/\/login/)
    await expect(page.getByText(TEST_USERS.user.email)).toBeVisible({ timeout: 5_000 })
  })
})

// ── Déconnexion ───────────────────────────────────────────────────────────────

test.describe('Déconnexion (Logout)', () => {

  test('déconnexion efface la session et redirige', async ({ page }) => {
    await loginAs(page, 'user')
    await page.goto('/profile')

    // Trouver et cliquer sur le bouton de déconnexion
    const logoutBtn = page.getByRole('button', { name: /déconnexion|logout|se déconnecter/i })
    await expect(logoutBtn).toBeVisible()
    await logoutBtn.click()

    // Après déconnexion : redirigé ou plus de session
    await expect(page).toHaveURL(/\/(login|)$/, { timeout: 5_000 })

    // Le token doit être supprimé du localStorage
    const token = await page.evaluate(() => localStorage.getItem('access_token'))
    expect(token).toBeNull()
  })

  test('accès à /profile après déconnexion redirige vers /login', async ({ page }) => {
    await loginAs(page, 'user')
    await clearAuth(page)
    await page.goto('/profile')
    await expect(page).toHaveURL(/\/login/, { timeout: 5_000 })
  })
})
