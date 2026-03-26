/**
 * Configuration globale pour les tests Vitest.
 *
 * Ce fichier est exécuté avant chaque fichier de test.
 * Il configure :
 * - @testing-library/jest-dom (matchers enrichis)
 * - Mocks globaux (fetch, localStorage, i18n, React Router)
 */

import '@testing-library/jest-dom'
import { vi, beforeEach, afterEach } from 'vitest'

// ── Mock de fetch global ──────────────────────────────────────────────────────
// Remplace fetch par un mock vi pour contrôler les réponses API dans les tests
global.fetch = vi.fn()

// ── Mock de localStorage ──────────────────────────────────────────────────────
const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
})

// ── Mock de matchMedia (Tailwind responsive) ──────────────────────────────────
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// ── Mock de react-i18next ─────────────────────────────────────────────────────
// Évite de charger les fichiers de traduction dans les tests
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,  // Retourne la clé comme traduction
    i18n: {
      changeLanguage: vi.fn(),
      language: 'fr',
    },
  }),
  Trans: ({ children }: { children: React.ReactNode }) => children,
  initReactI18next: { type: '3rdParty', init: vi.fn() },
}))

// ── Mock de react-helmet-async ────────────────────────────────────────────────
vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => children,
  HelmetProvider: ({ children }: { children: React.ReactNode }) => children,
}))

// ── Réinitialisation entre les tests ─────────────────────────────────────────
beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
})

afterEach(() => {
  vi.restoreAllMocks()
})
