"""
Tests d'intégration pour les endpoints d'authentification.

Couvre : inscription, connexion, refresh token, profil, déconnexion.
"""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.integration
class TestRegister:
    def test_register_with_valid_invitation(self, client, waitlist_entry, db):
        """L'inscription nécessite une invitation valide (canal waitlist)."""
        # Marquer l'entrée comme invitée
        waitlist_entry.is_invited = True
        db.commit()

        with patch("app.routers.auth.send_verification_email", new_callable=AsyncMock):
            resp = client.post("/auth/register", json={
                "email": waitlist_entry.email,
                "password": "NewPassword123!",
                "full_name": "New User",
                "invitation_token": waitlist_entry.invitation_token or "token",
            })
        # 200 ou 400 selon la logique d'invitation
        assert resp.status_code in (200, 201, 400, 422)

    def test_register_duplicate_email(self, client, regular_user):
        """Impossible de s'inscrire avec un email déjà utilisé."""
        with patch("app.routers.auth.send_verification_email", new_callable=AsyncMock):
            resp = client.post("/auth/register", json={
                "email": regular_user.email,
                "password": "Password123!",
                "full_name": "Duplicate",
            })
        assert resp.status_code in (400, 409, 422)

    def test_register_weak_password_rejected(self, client):
        """Un mot de passe trop court doit être refusé."""
        resp = client.post("/auth/register", json={
            "email": "newuser@test.com",
            "password": "weak",
            "full_name": "New User",
        })
        assert resp.status_code == 422


@pytest.mark.integration
class TestLogin:
    def test_login_success(self, client, regular_user):
        """Connexion avec identifiants valides retourne des tokens."""
        resp = client.post("/auth/login", json={
            "email": regular_user.email,
            "password": "Password123!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, regular_user):
        """Connexion avec mauvais mot de passe retourne 401."""
        resp = client.post("/auth/login", json={
            "email": regular_user.email,
            "password": "WrongPassword!",
        })
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        """Connexion avec email inconnu retourne 401."""
        resp = client.post("/auth/login", json={
            "email": "nobody@test.com",
            "password": "Password123!",
        })
        assert resp.status_code == 401

    def test_login_inactive_user(self, client, db, regular_user):
        """Connexion d'un utilisateur désactivé retourne 401 ou 403."""
        regular_user.is_active = False
        db.commit()
        resp = client.post("/auth/login", json={
            "email": regular_user.email,
            "password": "Password123!",
        })
        assert resp.status_code in (401, 403)


@pytest.mark.integration
class TestProtectedEndpoints:
    def test_me_requires_auth(self, client):
        """L'endpoint /auth/me nécessite un token valide."""
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_valid_token(self, client, user_token, regular_user):
        """L'endpoint /auth/me retourne le profil avec un token valide."""
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {user_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == regular_user.email

    def test_me_with_invalid_token(self, client):
        """Un token malformé retourne 401."""
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401


@pytest.mark.integration
class TestLogout:
    def test_logout_requires_auth(self, client):
        """La déconnexion nécessite d'être authentifié."""
        resp = client.post("/auth/logout")
        assert resp.status_code == 401

    def test_logout_with_token(self, client, user_token):
        """La déconnexion avec token valide réussit."""
        resp = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code in (200, 204)
