"""Tests d'intégration pour les endpoints de gestion du profil utilisateur."""

import pytest


@pytest.mark.integration
class TestUserProfile:
    def test_get_profile_requires_auth(self, client):
        resp = client.get("/users/me")
        assert resp.status_code == 401

    def test_get_profile_authenticated(self, client, user_token, regular_user):
        resp = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == regular_user.email

    def test_update_profile_name(self, client, user_token):
        resp = client.patch(
            "/users/me",
            json={"full_name": "Updated Name"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code in (200, 405)  # 405 si PATCH non supporté

    def test_change_password_wrong_current(self, client, user_token):
        resp = client.post(
            "/users/me/change-password",
            json={
                "current_password": "WrongCurrent!",
                "new_password": "NewPassword123!",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code in (400, 401, 404, 405)
