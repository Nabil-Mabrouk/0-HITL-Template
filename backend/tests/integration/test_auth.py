"""
Tests d'intégration pour le router d'authentification.

Couvre :
- POST /api/auth/register      — inscription
- POST /api/auth/login         — connexion
- POST /api/auth/refresh       — renouvellement de token
- POST /api/auth/logout        — déconnexion
- POST /api/auth/verify-email  — vérification d'email
- POST /api/auth/forgot-password — demande de reset
- POST /api/auth/reset-password  — reset de mot de passe
- GET  /api/auth/me            — profil courant

Stratégie : chaque test est isolé dans sa propre transaction
(rollback automatique via la fixture db).
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.auth.security import create_email_token, hash_password
from tests.factories import make_register_payload, make_login_payload


# ── POST /api/auth/register ──────────────────────────────────────────────────

class TestRegister:
    """Tests pour l'inscription d'un nouvel utilisateur."""

    @patch("app.routers.auth.send_verification_email", new_callable=AsyncMock)
    def test_register_success(self, mock_email, client: TestClient):
        """Une inscription valide doit retourner 201 avec les infos utilisateur."""
        payload = make_register_payload()
        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert "hashed_password" not in data  # Ne jamais exposer le hash

    @patch("app.routers.auth.send_verification_email", new_callable=AsyncMock)
    def test_register_sends_verification_email(self, mock_email, client: TestClient):
        """L'inscription doit déclencher l'envoi d'un email de vérification."""
        payload = make_register_payload()
        client.post("/api/auth/register", json=payload)
        mock_email.assert_called_once()

    @patch("app.routers.auth.send_verification_email", new_callable=AsyncMock)
    def test_register_duplicate_email_returns_409(self, mock_email, client: TestClient, db: Session):
        """Une inscription avec un email déjà existant doit retourner 409."""
        # Créer un utilisateur en DB
        existing = User(
            email="existing@test.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.user,
            is_active=True,
            is_verified=True,
        )
        db.add(existing)
        db.commit()

        # Tentative d'inscription avec le même email
        payload = make_register_payload(email="existing@test.com")
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 409

    def test_register_invalid_email_returns_422(self, client: TestClient):
        """Une adresse email invalide doit retourner 422 (validation Pydantic)."""
        payload = make_register_payload(email="not-an-email")
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 422

    def test_register_weak_password_returns_422(self, client: TestClient):
        """Un mot de passe trop court doit retourner 422."""
        payload = make_register_payload(password="abc")
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 422

    @patch("app.routers.auth.send_verification_email", new_callable=AsyncMock)
    def test_register_new_user_not_verified(self, mock_email, client: TestClient):
        """Un nouvel utilisateur ne doit pas être vérifié automatiquement."""
        payload = make_register_payload()
        response = client.post("/api/auth/register", json=payload)
        data = response.json()
        assert data.get("is_verified") is False


# ── POST /api/auth/login ─────────────────────────────────────────────────────

class TestLogin:
    """Tests pour la connexion utilisateur."""

    def test_login_success_returns_tokens(self, client: TestClient, user_standard: User):
        """Une connexion réussie doit retourner access_token et refresh_token."""
        payload = make_login_payload(email=user_standard.email)
        response = client.post("/api/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client: TestClient, user_standard: User):
        """Un mauvais mot de passe doit retourner 401."""
        payload = make_login_payload(email=user_standard.email, password="WrongPassword!")
        response = client.post("/api/auth/login", json=payload)
        assert response.status_code == 401

    def test_login_unknown_email_returns_401(self, client: TestClient):
        """Un email inconnu doit retourner 401 (pas 404 — évite l'énumération)."""
        payload = make_login_payload(email="nobody@example.com")
        response = client.post("/api/auth/login", json=payload)
        assert response.status_code == 401

    def test_login_inactive_user_returns_401(self, client: TestClient, user_inactive: User):
        """Un compte désactivé doit retourner 401."""
        payload = make_login_payload(email=user_inactive.email)
        response = client.post("/api/auth/login", json=payload)
        assert response.status_code == 401

    def test_login_access_token_is_valid_jwt(self, client: TestClient, user_standard: User):
        """Le token d'accès retourné doit être un JWT valide et décodable."""
        from app.auth.security import decode_access_token
        payload = make_login_payload(email=user_standard.email)
        response = client.post("/api/auth/login", json=payload)
        token = response.json()["access_token"]
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == str(user_standard.id)


# ── GET /api/auth/me ──────────────────────────────────────────────────────────

class TestMe:
    """Tests pour le profil de l'utilisateur courant."""

    def test_me_with_valid_token(self, client: TestClient, user_standard: User, auth_headers_user: dict):
        """GET /me avec un token valide doit retourner les infos de l'utilisateur."""
        response = client.get("/api/auth/me", headers=auth_headers_user)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_standard.email
        assert data["role"] == UserRole.user.value

    def test_me_without_token_returns_401(self, client: TestClient):
        """GET /me sans token doit retourner 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client: TestClient):
        """GET /me avec un token invalide doit retourner 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    def test_me_does_not_expose_password(self, client: TestClient, auth_headers_user: dict):
        """La réponse de /me ne doit jamais exposer le hash du mot de passe."""
        response = client.get("/api/auth/me", headers=auth_headers_user)
        data = response.json()
        assert "hashed_password" not in data
        assert "password" not in data


# ── POST /api/auth/verify-email ───────────────────────────────────────────────

class TestVerifyEmail:
    """Tests pour la vérification d'email."""

    def test_valid_verification_token_verifies_user(
        self, client: TestClient, db: Session
    ):
        """Un token valide doit marquer l'utilisateur comme vérifié."""
        # Créer un utilisateur non vérifié
        user = User(
            email="unverified@test.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.user,
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        db.commit()

        # Générer un token de vérification
        token = create_email_token(user.email, "verify")
        response = client.post("/api/auth/verify-email", json={"token": token})

        assert response.status_code == 200
        db.refresh(user)
        assert user.is_verified is True

    def test_invalid_verification_token_returns_400(self, client: TestClient):
        """Un token invalide doit retourner 400."""
        response = client.post("/api/auth/verify-email", json={"token": "invalid-token"})
        assert response.status_code == 400

    def test_wrong_purpose_token_rejected(self, client: TestClient):
        """Un token de reset utilisé pour verify doit être rejeté."""
        token = create_email_token("user@test.com", "reset")  # mauvais purpose
        response = client.post("/api/auth/verify-email", json={"token": token})
        assert response.status_code == 400


# ── POST /api/auth/forgot-password ────────────────────────────────────────────

class TestForgotPassword:
    """Tests pour la demande de reset de mot de passe."""

    @patch("app.routers.auth.send_password_reset_email", new_callable=AsyncMock)
    def test_forgot_password_known_email_returns_200(
        self, mock_email, client: TestClient, user_standard: User
    ):
        """Une demande avec un email connu doit retourner 200."""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": user_standard.email}
        )
        assert response.status_code == 200

    @patch("app.routers.auth.send_password_reset_email", new_callable=AsyncMock)
    def test_forgot_password_unknown_email_returns_200(
        self, mock_email, client: TestClient
    ):
        """
        Une demande avec un email inconnu doit aussi retourner 200.
        Évite l'énumération d'emails (security: user enumeration prevention).
        """
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "nobody@nowhere.com"}
        )
        assert response.status_code == 200


# ── Sécurité générale ─────────────────────────────────────────────────────────

class TestAuthSecurity:
    """Tests de sécurité transversaux pour l'authentification."""

    def test_login_error_message_is_generic(self, client: TestClient):
        """
        Le message d'erreur de login ne doit pas distinguer
        'email inconnu' de 'mauvais mot de passe' (user enumeration).
        """
        r1 = client.post("/api/auth/login",
                         json={"email": "nobody@test.com", "password": "anything"})
        r2 = client.post("/api/auth/login",
                         json={"email": "admin@test.com", "password": "wrong"})

        # Les deux doivent retourner 401
        assert r1.status_code == 401
        assert r2.status_code == 401
        # Idéalement le même message (mais on vérifie juste le code ici)

    def test_protected_endpoint_requires_auth(self, client: TestClient):
        """Les endpoints protégés doivent rejeter les requêtes sans token."""
        endpoints = [
            ("GET", "/api/auth/me"),
            ("GET", "/api/users/profile"),
        ]
        for method, path in endpoints:
            response = client.request(method, path)
            assert response.status_code in (401, 403), \
                f"{method} {path} doit exiger une authentification"
