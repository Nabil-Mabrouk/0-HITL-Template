"""Tests d'intégration pour les endpoints de la liste d'attente."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.integration
class TestWaitlist:
    def test_join_waitlist(self, client):
        """Inscription à la liste d'attente avec email valide."""
        with patch("app.routers.waitlist.send_waitlist_confirmation", new_callable=AsyncMock, create=True):
            resp = client.post("/waitlist/join", json={
                "email": "newwaiter@test.com",
                "full_name": "New Waiter",
            })
        assert resp.status_code in (200, 201, 409)

    def test_join_waitlist_duplicate(self, client, waitlist_entry):
        """Inscription avec un email déjà en liste retourne une erreur."""
        with patch("app.routers.waitlist.send_waitlist_confirmation", new_callable=AsyncMock, create=True):
            resp = client.post("/waitlist/join", json={
                "email": waitlist_entry.email,
                "full_name": "Duplicate",
            })
        assert resp.status_code in (400, 409)

    def test_join_waitlist_invalid_email(self, client):
        """Email invalide retourne 422."""
        resp = client.post("/waitlist/join", json={
            "email": "not-an-email",
            "full_name": "Invalid",
        })
        assert resp.status_code == 422

    def test_waitlist_admin_list_requires_auth(self, client):
        """La liste des inscrits n'est accessible qu'aux admins."""
        resp = client.get("/admin/waitlist")
        assert resp.status_code == 401

    def test_waitlist_admin_list_requires_admin_role(self, client, user_token):
        """Un utilisateur standard ne peut pas voir la liste d'attente."""
        resp = client.get(
            "/admin/waitlist",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code in (401, 403)

    def test_waitlist_admin_list_accessible_by_admin(self, client, admin_token):
        """Un admin peut voir la liste d'attente."""
        resp = client.get(
            "/admin/waitlist",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
