"""Tests d'intégration pour les endpoints d'administration."""

import pytest


@pytest.mark.integration
class TestAdminAccess:
    def test_admin_dashboard_requires_auth(self, client):
        resp = client.get("/admin/stats")
        assert resp.status_code == 401

    def test_admin_dashboard_requires_admin_role(self, client, user_token):
        resp = client.get(
            "/admin/stats",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code in (401, 403)

    def test_admin_dashboard_accessible_by_admin(self, client, admin_token):
        resp = client.get(
            "/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    def test_admin_users_list(self, client, admin_token):
        """L'admin peut lister les utilisateurs."""
        resp = client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200

    def test_admin_cannot_be_accessed_by_premium(self, client, db, premium_user):
        """Un utilisateur premium n'a pas accès à l'administration."""
        resp_login = client.post("/auth/login", json={
            "email": premium_user.email,
            "password": "Premium123!",
        })
        assert resp_login.status_code == 200
        token = resp_login.json()["access_token"]

        resp = client.get(
            "/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (401, 403)
