/**
 * Tests pour la page Login.tsx
 *
 * Couvre :
 * - Rendu du formulaire
 * - Soumission réussie → redirige vers /profile
 * - Soumission échouée → affiche le message d'erreur
 * - Désactivation du bouton pendant le chargement
 * - Lien "mot de passe oublié"
 */

import { describe, it, expect, vi } from 'vitest'
import { screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders, mockFetchResponse, mockFetchError } from '../../test/utils'

// Mock de AuthContext — on contrôle la fonction login
const mockLogin = vi.fn()
const mockNavigate = vi.fn()

vi.mock('../../context/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin,
    user: null,
    accessToken: null,
    isLoading: false,
    isAdmin: false,
    isPremium: false,
    logout: vi.fn(),
  }),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Import APRÈS les mocks
const { default: Login } = await import('../Login')

describe('Page Login', () => {

  describe('Rendu initial', () => {
    it('affiche le champ email', () => {
      renderWithProviders(<Login />)
      expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument()
    })

    it('affiche le champ mot de passe', () => {
      renderWithProviders(<Login />)
      expect(screen.getByPlaceholderText(/password|mot de passe/i)).toBeInTheDocument()
    })

    it('affiche le bouton de connexion', () => {
      renderWithProviders(<Login />)
      expect(screen.getByRole('button', { name: /login\.submit|se connecter/i })).toBeInTheDocument()
    })

    it('affiche le lien mot de passe oublié', () => {
      renderWithProviders(<Login />)
      const forgotLink = screen.getByRole('link', { name: /forgot|oublié/i })
      expect(forgotLink).toBeInTheDocument()
      expect(forgotLink).toHaveAttribute('href', '/forgot-password')
    })

    it('n\'affiche pas d\'erreur au départ', () => {
      renderWithProviders(<Login />)
      // Aucun message d'erreur visible initialement
      expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    })
  })

  describe('Connexion réussie', () => {
    it('appelle login() et redirige vers /profile', async () => {
      const user = userEvent.setup()
      mockFetchResponse({ access_token: 'jwt-token-123', refresh_token: 'refresh-456' })
      mockLogin.mockResolvedValueOnce(undefined)

      renderWithProviders(<Login />)

      await user.type(screen.getByPlaceholderText(/email/i), 'user@test.com')
      await user.type(screen.getByPlaceholderText(/password|mot de passe/i), 'Password123!')
      await user.click(screen.getByRole('button', { name: /login\.submit|se connecter/i }))

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('jwt-token-123')
        expect(mockNavigate).toHaveBeenCalledWith('/profile')
      })
    })
  })

  describe('Connexion échouée', () => {
    it('affiche le message d\'erreur du serveur', async () => {
      const user = userEvent.setup()
      mockFetchError(401, 'Identifiants incorrects')

      renderWithProviders(<Login />)

      await user.type(screen.getByPlaceholderText(/email/i), 'user@test.com')
      await user.type(screen.getByPlaceholderText(/password|mot de passe/i), 'WrongPassword!')
      await user.click(screen.getByRole('button', { name: /login\.submit|se connecter/i }))

      await waitFor(() => {
        expect(screen.getByText('Identifiants incorrects')).toBeInTheDocument()
      })
    })

    it('ne redirige pas en cas d\'échec', async () => {
      const user = userEvent.setup()
      mockFetchError(401, 'Erreur')

      renderWithProviders(<Login />)

      await user.type(screen.getByPlaceholderText(/email/i), 'user@test.com')
      await user.type(screen.getByPlaceholderText(/password|mot de passe/i), 'Wrong!')
      await user.click(screen.getByRole('button', { name: /login\.submit|se connecter/i }))

      await waitFor(() => {
        expect(mockNavigate).not.toHaveBeenCalled()
      })
    })
  })

  describe('État de chargement', () => {
    it('désactive le bouton pendant la soumission', async () => {
      const user = userEvent.setup()
      // Réponse lente (promise non résolue immédiatement)
      vi.mocked(global.fetch).mockImplementationOnce(
        () => new Promise(resolve => setTimeout(() => resolve({
          ok: true,
          json: async () => ({ access_token: 'token' }),
        } as Response), 500))
      )

      renderWithProviders(<Login />)

      await user.type(screen.getByPlaceholderText(/email/i), 'user@test.com')
      await user.type(screen.getByPlaceholderText(/password|mot de passe/i), 'Password123!')

      const submitBtn = screen.getByRole('button', { name: /login\.submit|se connecter/i })
      await user.click(submitBtn)

      expect(submitBtn).toBeDisabled()
    })
  })
})
