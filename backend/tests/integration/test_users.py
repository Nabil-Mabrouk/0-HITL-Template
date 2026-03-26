"""
Tests d'intégration pour le router utilisateurs.

Couvre :
- GET  /api/users/profile    — lire son profil
- PUT  /api/users/profile    — modifier son profil
- PUT  /api/users/password   — changer son mot de passe
- DELETE /api/users/account  — supprimer son compte
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.auth.security import hash_password


class TestGetProfile:
    """Tests pour la lecture du profil utilisateur."""

    def test_get_profile_authenticated(
        self, client: TestClient, user_standard: User, auth_headers_user: dict
    ):
        """Un utilisateur authentifié doit pouvoir lire son profil."""
        response = client.get("/api/users/profile", headers=auth_headers_user)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_standard.email

    def test_get_profile_unauthenticated_returns_401(self, client: TestClient):
        """Un utilisateur non authentifié ne doit pas accéder au profil."""
        response = client.get("/api/users/profile")
        assert response.status_code == 401

    def test_profile_does_not_expose_password_hash(
        self, client: TestClient, auth_headers_user: dict
    ):
        """Le profil ne doit jamais exposer le hash du mot de passe."""
        response = client.get("/api/users/profile", headers=auth_headers_user)
        data = response.json()
        assert "hashed_password" not in data
        assert "password" not in data


class TestUpdateProfile:
    """Tests pour la modification du profil."""

    def test_update_full_name(
        self, client: TestClient, auth_headers_user: dict
    ):
        """Un utilisateur doit pouvoir modifier son nom complet."""
        response = client.put(
            "/api/users/profile",
            json={"full_name": "Nouveau Nom"},
            headers=auth_headers_user,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Nouveau Nom"

    def test_update_profile_unauthenticated_returns_401(self, client: TestClient):
        """La modification de profil nécessite une authentification."""
        response = client.put("/api/users/profile", json={"full_name": "Test"})
        assert response.status_code == 401

    def test_cannot_change_own_role(
        self, client: TestClient, auth_headers_user: dict, user_standard: User, db: Session
    ):
        """Un utilisateur ne doit pas pouvoir s'élever à un rôle supérieur."""
        response = client.put(
            "/api/users/profile",
            json={"role": "admin"},  # tentative d'escalade de privilèges
            headers=auth_headers_user,
        )
        db.refresh(user_standard)
        # Le rôle ne doit pas avoir changé
        assert user_standard.role == UserRole.user


class TestChangePassword:
    """Tests pour le changement de mot de passe."""

    def test_change_password_success(
        self, client: TestClient, user_standard: User, auth_headers_user: dict, db: Session
    ):
        """Un utilisateur peut changer son mot de passe avec le bon ancien mot de passe."""
        response = client.put(
            "/api/users/password",
            json={
                "current_password": "Password123!",
                "new_password": "NewPassword456!",
            },
            headers=auth_headers_user,
        )
        assert response.status_code == 200

    def test_change_password_wrong_current(
        self, client: TestClient, auth_headers_user: dict
    ):
        """Un mauvais mot de passe actuel doit retourner 400 ou 401."""
        response = client.put(
            "/api/users/password",
            json={
                "current_password": "WrongPassword!",
                "new_password": "NewPassword456!",
            },
            headers=auth_headers_user,
        )
        assert response.status_code in (400, 401)

    def test_change_password_requires_auth(self, client: TestClient):
        """Le changement de mot de passe nécessite une authentification."""
        response = client.put(
            "/api/users/password",
            json={"current_password": "old", "new_password": "new"},
        )
        assert response.status_code == 401


class TestDeleteAccount:
    """Tests pour la suppression de compte."""

    def test_delete_account_requires_auth(self, client: TestClient):
        """La suppression de compte nécessite une authentification."""
        response = client.delete("/api/users/account")
        assert response.status_code == 401

    def test_user_cannot_delete_other_user(
        self,
        client: TestClient,
        user_standard: User,
        user_premium: User,
        auth_headers_user: dict,
    ):
        """Un utilisateur ne doit pas pouvoir supprimer le compte d'un autre."""
        # Tenter de supprimer le compte premium via l'URL (si endpoint avec ID)
        response = client.delete(
            f"/api/users/{user_premium.id}",
            headers=auth_headers_user,
        )
        # Doit retourner 403 ou 404 (pas 200)
        assert response.status_code in (403, 404, 405)
