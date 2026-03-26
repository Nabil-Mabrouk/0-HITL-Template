"""
Tests unitaires pour le module app.auth.security.

Ces tests vérifient le comportement des fonctions de hachage,
de vérification de mots de passe et de gestion des tokens JWT/email.
Aucune base de données ni serveur HTTP n'est nécessaire.
"""

import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars-for-jwt-signing")

import time
import pytest
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    create_email_token,
    decode_email_token,
)


# ── Tests hash_password ───────────────────────────────────────────────────────

@pytest.mark.unit
class TestHashPassword:
    def test_returns_bcrypt_hash(self):
        h = hash_password("securePass1!")
        assert h.startswith("$2b$")

    def test_different_salts_each_call(self):
        h1 = hash_password("securePass1!")
        h2 = hash_password("securePass1!")
        assert h1 != h2

    def test_rejects_empty_password(self):
        with pytest.raises(ValueError):
            hash_password("")

    def test_rejects_short_password(self):
        with pytest.raises(ValueError):
            hash_password("abc")

    def test_accepts_minimum_length(self):
        h = hash_password("abcdefgh")
        assert h.startswith("$2b$")


# ── Tests verify_password ─────────────────────────────────────────────────────

@pytest.mark.unit
class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        h = hash_password("myPassword1!")
        assert verify_password("myPassword1!", h) is True

    def test_wrong_password_returns_false(self):
        h = hash_password("myPassword1!")
        assert verify_password("wrongPassword", h) is False

    def test_empty_plain_returns_false(self):
        h = hash_password("myPassword1!")
        assert verify_password("", h) is False

    def test_empty_hash_returns_false(self):
        assert verify_password("myPassword1!", "") is False

    def test_case_sensitive(self):
        h = hash_password("MyPassword1!")
        assert verify_password("mypassword1!", h) is False


# ── Tests create_access_token / decode_access_token ───────────────────────────

@pytest.mark.unit
class TestAccessToken:
    def test_creates_valid_token(self):
        token = create_access_token({"sub": "42"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_returns_payload(self):
        token = create_access_token({"sub": "42"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_tampered_token_returns_none(self):
        token = create_access_token({"sub": "42"})
        tampered = token[:-5] + "XXXXX"
        assert decode_access_token(tampered) is None

    def test_invalid_token_returns_none(self):
        assert decode_access_token("not.a.token") is None

    def test_empty_token_returns_none(self):
        assert decode_access_token("") is None


# ── Tests create_refresh_token ────────────────────────────────────────────────

@pytest.mark.unit
class TestRefreshToken:
    def test_returns_string(self):
        token = create_refresh_token()
        assert isinstance(token, str)

    def test_sufficient_length(self):
        token = create_refresh_token()
        assert len(token) > 50

    def test_unique_each_call(self):
        tokens = {create_refresh_token() for _ in range(10)}
        assert len(tokens) == 10


# ── Tests create_email_token / decode_email_token ─────────────────────────────

@pytest.mark.unit
class TestEmailToken:
    def test_verify_token_roundtrip(self):
        token = create_email_token("user@example.com", "verify")
        email = decode_email_token(token, "verify")
        assert email == "user@example.com"

    def test_reset_token_roundtrip(self):
        token = create_email_token("user@example.com", "reset")
        email = decode_email_token(token, "reset")
        assert email == "user@example.com"

    def test_wrong_purpose_returns_none(self):
        token = create_email_token("user@example.com", "verify")
        assert decode_email_token(token, "reset") is None

    def test_invalid_token_returns_none(self):
        assert decode_email_token("invalid.token.here", "verify") is None
