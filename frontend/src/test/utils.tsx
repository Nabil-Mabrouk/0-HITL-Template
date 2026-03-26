/**
 * Utilitaires de test pour React Testing Library.
 *
 * Fournit :
 * - renderWithProviders() : render avec tous les Context providers
 * - createMockUser() : factory d'utilisateur de test
 * - mockFetchResponse() : helper pour mocker fetch
 * - mockFetchError() : helper pour simuler une erreur API
 */

import React from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface MockUser {
  id: number
  email: string
  full_name: string | null
  role: 'anonymous' | 'waitlist' | 'user' | 'premium' | 'admin'
  is_active: boolean
  is_verified: boolean
}

// ── Factory d'utilisateurs de test ────────────────────────────────────────────

export function createMockUser(overrides: Partial<MockUser> = {}): MockUser {
  return {
    id: 1,
    email: 'user@test.com',
    full_name: 'Test User',
    role: 'user',
    is_active: true,
    is_verified: true,
    ...overrides,
  }
}

export const mockAdminUser = createMockUser({ role: 'admin', email: 'admin@test.com' })
export const mockPremiumUser = createMockUser({ role: 'premium', email: 'premium@test.com' })
export const mockStandardUser = createMockUser({ role: 'user' })

// ── Wrapper de providers ──────────────────────────────────────────────────────

interface ProvidersProps {
  children: React.ReactNode
  initialAuthToken?: string
}

/**
 * Wrapper qui fournit tous les Context providers nécessaires.
 * À utiliser dans renderWithProviders().
 */
function AllProviders({ children }: ProvidersProps) {
  return (
    <BrowserRouter>
      {children}
    </BrowserRouter>
  )
}

// ── renderWithProviders ───────────────────────────────────────────────────────

interface RenderWithProvidersOptions extends RenderOptions {
  initialAuthToken?: string
}

/**
 * Remplace le render standard de RTL avec tous les providers.
 *
 * Usage :
 *   const { getByText } = renderWithProviders(<MyComponent />)
 */
export function renderWithProviders(
  ui: React.ReactElement,
  options: RenderWithProvidersOptions = {},
): RenderResult {
  const { initialAuthToken, ...renderOptions } = options

  if (initialAuthToken) {
    localStorage.setItem('access_token', initialAuthToken)
  }

  return render(ui, {
    wrapper: ({ children }) => (
      <AllProviders initialAuthToken={initialAuthToken}>
        {children}
      </AllProviders>
    ),
    ...renderOptions,
  })
}

// ── Helpers fetch mock ────────────────────────────────────────────────────────

/**
 * Configure fetch pour retourner une réponse JSON réussie.
 *
 * Usage :
 *   mockFetchResponse({ id: 1, email: 'user@test.com' })
 */
export function mockFetchResponse<T>(data: T, status = 200): void {
  vi.mocked(global.fetch).mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
    headers: new Headers({ 'Content-Type': 'application/json' }),
  } as Response)
}

/**
 * Configure fetch pour simuler une erreur réseau.
 */
export function mockFetchNetworkError(message = 'Network error'): void {
  vi.mocked(global.fetch).mockRejectedValueOnce(new Error(message))
}

/**
 * Configure fetch pour retourner une erreur HTTP avec message.
 */
export function mockFetchError(status: number, detail: string): void {
  vi.mocked(global.fetch).mockResolvedValueOnce({
    ok: false,
    status,
    json: async () => ({ detail }),
    text: async () => JSON.stringify({ detail }),
    headers: new Headers({ 'Content-Type': 'application/json' }),
  } as Response)
}

// ── Re-exports de RTL ─────────────────────────────────────────────────────────
// Permet d'importer tout depuis utils.tsx au lieu de @testing-library/react
export { screen, fireEvent, waitFor, within, act } from '@testing-library/react'
export { userEvent } from '@testing-library/user-event'
