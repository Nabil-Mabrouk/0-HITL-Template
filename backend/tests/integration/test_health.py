"""Tests d'intégration : endpoints de santé et status de l'API."""

import pytest


@pytest.mark.integration
class TestHealth:
    def test_root_responds(self, client):
        resp = client.get("/")
        assert resp.status_code in (200, 404)  # Selon si un root endpoint est défini

    def test_docs_available_in_test(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_openapi_schema_available(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "openapi" in schema
        assert "paths" in schema
