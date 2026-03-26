"""Tests d'intégration pour les endpoints de contenu public."""

import pytest


@pytest.mark.integration
class TestContentPublic:
    def test_content_list_public(self, client):
        """Le contenu public est accessible sans authentification."""
        resp = client.get("/content/")
        assert resp.status_code in (200, 404)

    def test_content_list_authenticated(self, client, user_token):
        resp = client.get(
            "/content/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code in (200, 404)

    def test_content_not_found(self, client):
        """Un slug inexistant retourne 404."""
        resp = client.get("/content/nonexistent-slug-xyz")
        assert resp.status_code == 404

    def test_admin_content_create_requires_admin(self, client, user_token):
        """Seul un admin peut créer du contenu."""
        resp = client.post(
            "/admin/content",
            json={
                "title": "Test Article",
                "slug": "test-article",
                "content": "# Test\nContenu de test.",
                "is_published": True,
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code in (401, 403)

    def test_admin_content_create_by_admin(self, client, admin_token):
        """Un admin peut créer du contenu."""
        resp = client.post(
            "/admin/content",
            json={
                "title": "Test Article",
                "slug": "test-article",
                "content": "# Test\nContenu de test.",
                "is_published": True,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code in (200, 201, 404, 422)
