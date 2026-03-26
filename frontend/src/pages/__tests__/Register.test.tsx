/**
 * Tests pour la page Register.tsx
 *
 * Couvre :
 * - Sans token d'invitation : affiche le message d'accès refusé
 * - Avec token d'invitation : affiche le formulaire d'inscription
 * - Soumission réussie : affiche l'écran de confirmation
 * - Soumission échouée : affiche le message d'erreur
 */

import { describe, it, expect, vi } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders, mockFetchResponse, mockFetchError } from '../../test/utils'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [new URLSearchParams('?invitation=valid-token-123')],
  }
})

const { default: Register } = await import('../Register')

// ── Sans token d'invitation ───────────────────────────────────────────────────

describe('Page Register — sans token d\'invitation', () => {
  beforeEach(() => {
    vi.mock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom')
      return {
        ...actual,
        useNavigate: () => mockNavigate,
        useSearchParams: () => [new URLSearchParams('')],  // Pas de token
      }
    })
  })

  it('affiche le message d\'accès refusé', async () => {
    const { default: RegisterNoToken } = await import('../Register')
    renderWithProviders(<RegisterNoToken />)
    expect(
      screen.getByText(/register\.access_denied|accès refusé/i)
    ).toBeInTheDocument()
  })
})

// ── Avec token d'invitation ───────────────────────────────────────────────────

describe('Page Register — avec token d\'invitation', () => {

  it('affiche le formulaire d\'inscription', () => {
    renderWithProviders(<Register />)
    expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/password|mot de passe/i)).toBeInTheDocument()
  })

  it('affiche le champ nom complet', () => {
    renderWithProviders(<Register />)
    expect(screen.getByPlaceholderText(/full.name|nom/i)).toBeInTheDocument()
  })

  describe('Inscription réussie', () => {
    it('affiche l\'écran de confirmation après inscription', async () => {
      const user = userEvent.setup()
      mockFetchResponse({ id: 1, email: 'new@test.com' }, 201)

      renderWithProviders(<Register />)

      await user.type(screen.getByPlaceholderText(/full.name|nom/i), 'Nouveau User')
      await user.type(screen.getByPlaceholderText(/email/i), 'new@test.com')
      await user.type(screen.getByPlaceholderText(/password|mot de passe/i), 'Password123!')
      await user.click(screen.getByRole('button', { name: /register\.submit|créer/i }))

      await waitFor(() => {
        expect(
          screen.getByText(/register\.success_title|inscription confirmée|vérifiez/i)
        ).toBeInTheDocument()
      })
    })
  })

  describe('Inscription échouée', () => {
    it('affiche l\'erreur si l\'email est déjà utilisé', async () => {
      const user = userEvent.setup()
      mockFetchError(409, 'Email déjà utilisé')

      renderWithProviders(<Register />)

      await user.type(screen.getByPlaceholderText(/email/i), 'existing@test.com')
      await user.type(screen.getByPlaceholderText(/password|mot de passe/i), 'Password123!')
      await user.click(screen.getByRole('button', { name: /register\.submit|créer/i }))

      await waitFor(() => {
        expect(screen.getByText('Email déjà utilisé')).toBeInTheDocument()
      })
    })
  })
})
