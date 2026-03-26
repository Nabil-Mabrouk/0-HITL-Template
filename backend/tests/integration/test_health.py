"""
Tests d'intégration pour le endpoint /health.

Simple mais critique : valide que l'API démarre correctement
et que la base de données est accessible.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests pour GET /health."""

    def test_health_returns_200(self, client: TestClient):
        """Le health check doit retourner HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status_ok(self, client: TestClient):
        """Le champ status doit être 'ok' quand tout fonctionne."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_database_ok(self, client: TestClient):
        """Le champ database doit être 'ok' quand la DB répond."""
        response = client.get("/health")
        data = response.json()
        assert data["database"] == "ok"

    def test_health_has_version(self, client: TestClient):
        """La réponse doit inclure la version de l'API."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)
