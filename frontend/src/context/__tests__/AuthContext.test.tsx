/**
 * Tests pour AuthContext — gestion de l'état d'authentification.
 *
 * Couvre :
 * - État initial (pas de token en localStorage)
 * - login() : stocke le token, charge le profil
 * - logout() : efface le token, réinitialise l'utilisateur
 * - isAdmin / isPremium : drapeaux de rôle
 * - Recharge automatique depuis localStorage
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider, useAuth } from '../AuthContext'
import { mockFetchResponse, mockFetchError, createMockUser } from '../../test/utils'

// ── Composant de test pour accéder au contexte ────────────────────────────────

function TestConsumer() {
  const { user, isAdmin, isPremium, isLoading, accessToken } = useAuth()
  if (isLoading) return <div data-testid="loading">Chargement...</div>
  return (
    <div>
      <div data-testid="user-email">{user?.email ?? 'not-logged-in'}</div>
      <div data-testid="user-role">{user?.role ?? 'none'}</div>
      <div data-testid="is-admin">{String(isAdmin)}</div>
      <div data-testid="is-premium">{String(isPremium)}</div>
      <div data-testid="has-token">{String(!!accessToken)}</div>
    </div>
  )
}

function LoginConsumer() {
  const { login } = useAuth()
  return (
    <button onClick={() => login('test-token')}>
      Se connecter
    </button>
  )
}

function LogoutConsumer() {
  const { logout } = useAuth()
  return <button onClick={() => logout()}>Se déconnecter</button>
}

// ── Helper de render ──────────────────────────────────────────────────────────

function renderWithAuth(children: React.ReactNode) {
  return render(
    <BrowserRouter>
      <AuthProvider>{children}</AuthProvider>
    </BrowserRouter>
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('AuthContext', () => {

  describe('État initial — pas de token', () => {
    it('affiche le state de chargement puis "not-logged-in"', async () => {
      renderWithAuth(<TestConsumer />)
      await waitFor(() => {
        expect(screen.getByTestId('user-email').textContent).toBe('not-logged-in')
      })
    })

    it('isAdmin est false sans token', async () => {
      renderWithAuth(<TestConsumer />)
      await waitFor(() => {
        expect(screen.getByTestId('is-admin').textContent).toBe('false')
      })
    })

    it('isPremium est false sans token', async () => {
      renderWithAuth(<TestConsumer />)
      await waitFor(() => {
        expect(screen.getByTestId('is-premium').textContent).toBe('false')
      })
    })
  })

  describe('login()', () => {
    it('stocke le token et charge le profil utilisateur', async () => {
      const mockUser = createMockUser({ email: 'logged@test.com', role: 'user' })
      // Mock: fetchProfile retournera ce user
      mockFetchResponse(mockUser)

      renderWithAuth(
        <>
          <TestConsumer />
          <LoginConsumer />
        </>
      )

      await waitFor(() => expect(screen.queryByTestId('loading')).not.toBeInTheDocument())

      await act(async () => {
        screen.getByText('Se connecter').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('user-email').textContent).toBe('logged@test.com')
      })

      expect(localStorage.getItem('access_token')).toBe('test-token')
    })
  })

  describe('logout()', () => {
    it('efface le token et l\'utilisateur', async () => {
      localStorage.setItem('access_token', 'existing-token')
      const mockUser = createMockUser()
      mockFetchResponse(mockUser)  // pour fetchProfile au mount
      vi.mocked(global.fetch).mockResolvedValueOnce({
        ok: true, status: 200, json: async () => ({}),
      } as Response)

      renderWithAuth(
        <>
          <TestConsumer />
          <LogoutConsumer />
        </>
      )

      await waitFor(() => expect(screen.queryByTestId('loading')).not.toBeInTheDocument())

      await act(async () => {
        screen.getByText('Se déconnecter').click()
      })

      await waitFor(() => {
        expect(screen.getByTestId('user-email').textContent).toBe('not-logged-in')
        expect(localStorage.getItem('access_token')).toBeNull()
      })
    })
  })

  describe('Rôles isAdmin / isPremium', () => {
    it('isAdmin est true pour un admin', async () => {
      localStorage.setItem('access_token', 'admin-token')
      mockFetchResponse(createMockUser({ role: 'admin' }))

      renderWithAuth(<TestConsumer />)

      await waitFor(() => {
        expect(screen.getByTestId('is-admin').textContent).toBe('true')
      })
    })

    it('isPremium est true pour un utilisateur premium', async () => {
      localStorage.setItem('access_token', 'premium-token')
      mockFetchResponse(createMockUser({ role: 'premium' }))

      renderWithAuth(<TestConsumer />)

      await waitFor(() => {
        expect(screen.getByTestId('is-premium').textContent).toBe('true')
      })
    })

    it('isPremium est true pour un admin (hiérarchie des rôles)', async () => {
      localStorage.setItem('access_token', 'admin-token')
      mockFetchResponse(createMockUser({ role: 'admin' }))

      renderWithAuth(<TestConsumer />)

      await waitFor(() => {
        expect(screen.getByTestId('is-premium').textContent).toBe('true')
      })
    })

    it('isPremium est false pour un user standard', async () => {
      localStorage.setItem('access_token', 'user-token')
      mockFetchResponse(createMockUser({ role: 'user' }))

      renderWithAuth(<TestConsumer />)

      await waitFor(() => {
        expect(screen.getByTestId('is-premium').textContent).toBe('false')
      })
    })
  })

  describe('Token invalide', () => {
    it('efface le token si fetchProfile retourne une erreur', async () => {
      localStorage.setItem('access_token', 'expired-token')
      mockFetchError(401, 'Token invalide ou expiré')

      renderWithAuth(<TestConsumer />)

      await waitFor(() => {
        expect(screen.getByTestId('user-email').textContent).toBe('not-logged-in')
        expect(localStorage.getItem('access_token')).toBeNull()
      })
    })
  })

  describe('useAuth() hors AuthProvider', () => {
    it('lève une erreur si utilisé hors du provider', () => {
      // Capturer l'erreur de console
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      expect(() => {
        render(
          <BrowserRouter>
            <TestConsumer />
          </BrowserRouter>
        )
      }).toThrow('useAuth must be used within AuthProvider')
      consoleSpy.mockRestore()
    })
  })
})
