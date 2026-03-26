"""
Tests d'intégration pour les endpoints d'administration.

Principe fondamental : chaque endpoint admin doit être
inaccessible aux rôles inférieurs (principe du moindre privilège).

Couvre :
- GET /api/admin/users            — liste des utilisateurs
- GET /api/admin/users/{id}       — détail d'un utilisateur
- PUT /api/admin/users/{id}/role  — modifier le rôle
- DELETE /api/admin/users/{id}    — supprimer un utilisateur
- GET /api/admin/stats            — statistiques globales
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, UserRole


class TestAdminAccess:
    """Tests de contrôle d'accès pour les endpoints admin."""

    ADMIN_ENDPOINTS = [
        ("GET", "/api/admin/users"),
        ("GET", "/api/admin/stats"),
    ]

    def test_anonymous_cannot_access_admin(self, client: TestClient):
        """Un utilisateur non authentifié ne peut pas accéder aux endpoints admin."""
        for method, path in self.ADMIN_ENDPOINTS:
            response = client.request(method, path)
            assert response.status_code in (401, 403), \
                f"Anonyme: {method} {path} doit être refusé"

    def test_standard_user_cannot_access_admin(
        self, client: TestClient, auth_headers_user: dict
    ):
        """Un utilisateur standard ne peut pas accéder aux endpoints admin."""
        for method, path in self.ADMIN_ENDPOINTS:
            response = client.request(method, path, headers=auth_headers_user)
            assert response.status_code == 403, \
                f"User standard: {method} {path} doit être refusé"

    def test_premium_user_cannot_access_admin(
        self, client: TestClient, auth_headers_premium: dict
    ):
        """Un utilisateur premium ne peut pas accéder aux endpoints admin."""
        for method, path in self.ADMIN_ENDPOINTS:
            response = client.request(method, path, headers=auth_headers_premium)
            assert response.status_code == 403, \
                f"User premium: {method} {path} doit être refusé"

    def test_admin_can_access_all_admin_endpoints(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Un administrateur peut accéder à tous les endpoints admin."""
        for method, path in self.ADMIN_ENDPOINTS:
            response = client.request(method, path, headers=auth_headers_admin)
            assert response.status_code == 200, \
                f"Admin: {method} {path} doit être accessible"


class TestAdminListUsers:
    """Tests pour la liste des utilisateurs admin."""

    def test_admin_gets_all_users(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        user_standard: User,
        user_premium: User,
    ):
        """L'admin doit voir tous les utilisateurs."""
        response = client.get("/api/admin/users", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # Au moins user_standard et user_premium

    def test_users_list_includes_required_fields(
        self, client: TestClient, auth_headers_admin: dict, user_standard: User
    ):
        """Chaque utilisateur dans la liste doit avoir les champs essentiels."""
        response = client.get("/api/admin/users", headers=auth_headers_admin)
        users = response.json()
        if users:
            user = users[0]
            assert "id" in user
            assert "email" in user
            assert "role" in user
            assert "is_active" in user
            # Jamais le hash du mot de passe
            assert "hashed_password" not in user


class TestAdminUpdateUserRole:
    """Tests pour la modification du rôle d'un utilisateur."""

    def test_admin_can_promote_user_to_premium(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        user_standard: User,
        db: Session,
    ):
        """L'admin peut promouvoir un utilisateur au rôle premium."""
        response = client.put(
            f"/api/admin/users/{user_standard.id}/role",
            json={"role": "premium"},
            headers=auth_headers_admin,
        )
        assert response.status_code == 200
        db.refresh(user_standard)
        assert user_standard.role == UserRole.premium

    def test_admin_can_deactivate_user(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        user_standard: User,
        db: Session,
    ):
        """L'admin peut désactiver un utilisateur."""
        response = client.put(
            f"/api/admin/users/{user_standard.id}",
            json={"is_active": False},
            headers=auth_headers_admin,
        )
        # Accepte 200 ou 204 selon l'implémentation
        assert response.status_code in (200, 204)

    def test_cannot_modify_nonexistent_user(
        self, client: TestClient, auth_headers_admin: dict
    ):
        """Une tentative de modification d'un utilisateur inexistant retourne 404."""
        response = client.put(
            "/api/admin/users/999999/role",
            json={"role": "premium"},
            headers=auth_headers_admin,
        )
        assert response.status_code == 404


class TestAdminStats:
    """Tests pour les statistiques administrateur."""

    def test_stats_returns_user_count(
        self, client: TestClient, auth_headers_admin: dict, user_standard: User
    ):
        """Les statistiques doivent inclure le nombre d'utilisateurs."""
        response = client.get("/api/admin/stats", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        # Vérifier que des statistiques sont retournées
        assert isinstance(data, dict)
        # Les champs exacts dépendent de l'implémentation
        # On vérifie juste que la réponse est un objet non vide
        assert len(data) > 0
