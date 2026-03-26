"""
Tests d'intégration pour la liste d'attente.

Couvre :
- POST /api/waitlist/join          — s'inscrire à la liste d'attente
- GET  /api/admin/waitlist         — lire la liste (admin seulement)
- POST /api/admin/waitlist/invite  — inviter un email
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import WaitlistEntry


class TestJoinWaitlist:
    """Tests pour l'inscription à la liste d'attente."""

    def test_join_with_valid_email(self, client: TestClient):
        """Une inscription valide doit retourner 201."""
        response = client.post(
            "/api/waitlist/join",
            json={"email": "newuser@example.com"},
        )
        assert response.status_code == 201

    def test_join_with_invalid_email_returns_422(self, client: TestClient):
        """Un email invalide doit retourner 422."""
        response = client.post(
            "/api/waitlist/join",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422

    def test_join_duplicate_email_returns_409(
        self, client: TestClient, db: Session
    ):
        """Un email déjà en liste d'attente doit retourner 409."""
        # Ajouter manuellement en DB
        entry = WaitlistEntry(email="duplicate@test.com")
        db.add(entry)
        db.commit()

        # Tenter de rejoindre avec le même email
        response = client.post(
            "/api/waitlist/join",
            json={"email": "duplicate@test.com"},
        )
        assert response.status_code == 409

    def test_join_stores_email_in_db(self, client: TestClient, db: Session):
        """L'email doit être persisté en base de données."""
        email = "stored@example.com"
        client.post("/api/waitlist/join", json={"email": email})

        entry = db.query(WaitlistEntry).filter(
            WaitlistEntry.email == email
        ).first()
        assert entry is not None
        assert entry.email == email

    def test_join_new_entry_not_yet_invited(self, client: TestClient, db: Session):
        """Un nouvel inscrit ne doit pas encore avoir d'invitation."""
        email = "noinvite@example.com"
        client.post("/api/waitlist/join", json={"email": email})

        entry = db.query(WaitlistEntry).filter(
            WaitlistEntry.email == email
        ).first()
        assert entry.invited_at is None
        assert entry.invitation_token is None


class TestAdminWaitlist:
    """Tests admin pour la gestion de la liste d'attente."""

    def test_list_waitlist_requires_admin(
        self, client: TestClient, auth_headers_user: dict
    ):
        """Un non-admin ne peut pas voir la liste d'attente."""
        response = client.get("/api/admin/waitlist", headers=auth_headers_user)
        assert response.status_code == 403

    def test_admin_can_list_waitlist(
        self,
        client: TestClient,
        auth_headers_admin: dict,
        db: Session,
    ):
        """L'admin peut lister les entrées de la liste d'attente."""
        # Ajouter une entrée
        entry = WaitlistEntry(email="listed@test.com")
        db.add(entry)
        db.commit()

        response = client.get("/api/admin/waitlist", headers=auth_headers_admin)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
