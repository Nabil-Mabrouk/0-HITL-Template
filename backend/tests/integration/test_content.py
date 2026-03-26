"""
Tests d'intégration pour les routers de contenu (tutorials, leçons).

Couvre :
- GET /api/content/tutorials         — liste des tutorials
- GET /api/content/tutorials/{slug}  — détail d'un tutorial
- GET /api/content/tutorials/{slug}/lessons/{lesson_slug} — contenu d'une leçon

Stratégie de test par rôle :
- Anonyme/non authentifié : accès refusé
- User standard : accès tutorials libres, refus premium
- Premium : accès à tout
- Admin : accès à tout
"""

import pytest
from fastapi.testclient import TestClient

from app.models import User, Tutorial, Lesson


class TestListTutorials:
    """Tests pour la liste des tutorials."""

    def test_list_tutorials_requires_auth(self, client: TestClient):
        """La liste des tutorials nécessite d'être authentifié."""
        response = client.get("/api/content/tutorials")
        assert response.status_code in (401, 403)

    def test_user_can_list_tutorials(
        self, client: TestClient, tutorial_free: Tutorial, auth_headers_user: dict
    ):
        """Un utilisateur authentifié peut lister les tutorials."""
        response = client.get("/api/content/tutorials", headers=auth_headers_user)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_returns_only_published(
        self,
        client: TestClient,
        db,
        user_admin: User,
        auth_headers_user: dict,
    ):
        """Seuls les tutorials publiés doivent apparaître."""
        from app.models import Tutorial, AccessRole
        draft = Tutorial(
            title="Draft Tutorial",
            slug="draft-tutorial",
            access_role=AccessRole.user,
            is_published=False,
            lang="fr",
            author_id=user_admin.id,
        )
        db.add(draft)
        db.commit()

        response = client.get("/api/content/tutorials", headers=auth_headers_user)
        data = response.json()
        slugs = [t["slug"] for t in data]
        assert "draft-tutorial" not in slugs


class TestGetTutorial:
    """Tests pour le détail d'un tutorial."""

    def test_user_can_access_free_tutorial(
        self,
        client: TestClient,
        tutorial_free: Tutorial,
        auth_headers_user: dict,
    ):
        """Un user standard peut accéder à un tutorial libre."""
        response = client.get(
            f"/api/content/tutorials/{tutorial_free.slug}",
            headers=auth_headers_user,
        )
        assert response.status_code == 200

    def test_user_cannot_access_premium_tutorial(
        self,
        client: TestClient,
        tutorial_premium: Tutorial,
        auth_headers_user: dict,
    ):
        """Un user standard ne peut pas accéder à un tutorial premium."""
        response = client.get(
            f"/api/content/tutorials/{tutorial_premium.slug}",
            headers=auth_headers_user,
        )
        assert response.status_code == 403

    def test_premium_user_can_access_premium_tutorial(
        self,
        client: TestClient,
        tutorial_premium: Tutorial,
        auth_headers_premium: dict,
    ):
        """Un utilisateur premium peut accéder aux tutorials premium."""
        response = client.get(
            f"/api/content/tutorials/{tutorial_premium.slug}",
            headers=auth_headers_premium,
        )
        assert response.status_code == 200

    def test_admin_can_access_premium_tutorial(
        self,
        client: TestClient,
        tutorial_premium: Tutorial,
        auth_headers_admin: dict,
    ):
        """Un admin peut accéder à tous les tutorials."""
        response = client.get(
            f"/api/content/tutorials/{tutorial_premium.slug}",
            headers=auth_headers_admin,
        )
        assert response.status_code == 200

    def test_nonexistent_tutorial_returns_404(
        self, client: TestClient, auth_headers_user: dict
    ):
        """Un tutorial inexistant doit retourner 404."""
        response = client.get(
            "/api/content/tutorials/this-does-not-exist",
            headers=auth_headers_user,
        )
        assert response.status_code == 404


class TestGetLesson:
    """Tests pour le contenu d'une leçon."""

    def test_user_can_access_lesson_in_free_tutorial(
        self,
        client: TestClient,
        tutorial_free: Tutorial,
        lesson: Lesson,
        auth_headers_user: dict,
    ):
        """Un user peut lire une leçon dans un tutorial libre."""
        response = client.get(
            f"/api/content/tutorials/{tutorial_free.slug}/lessons/{lesson.slug}",
            headers=auth_headers_user,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == lesson.title

    def test_lesson_response_has_content(
        self,
        client: TestClient,
        tutorial_free: Tutorial,
        lesson: Lesson,
        auth_headers_user: dict,
    ):
        """La réponse d'une leçon doit inclure le contenu Markdown."""
        response = client.get(
            f"/api/content/tutorials/{tutorial_free.slug}/lessons/{lesson.slug}",
            headers=auth_headers_user,
        )
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 0

    def test_unauthenticated_cannot_access_lesson(
        self,
        client: TestClient,
        tutorial_free: Tutorial,
        lesson: Lesson,
    ):
        """Un utilisateur non authentifié ne peut pas accéder aux leçons."""
        response = client.get(
            f"/api/content/tutorials/{tutorial_free.slug}/lessons/{lesson.slug}",
        )
        assert response.status_code in (401, 403)
