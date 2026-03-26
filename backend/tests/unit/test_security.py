"""
Tests unitaires pour app/auth/security.py

Couvre :
- hash_password / verify_password
- create_access_token / decode_access_token
- create_refresh_token
- create_email_token / decode_email_token
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_refresh_token,
    create_email_token,
    decode_email_token,
)


# ── hash_password ─────────────────────────────────────────────────────────────

class TestHashPassword:
    """Tests pour la fonction de hachage de mots de passe."""

    def test_hash_returns_bcrypt_format(self):
        """Le hash doit commencer par $2b$ (format bcrypt)."""
        hashed = hash_password("Password123!")
        assert hashed.startswith("$2b$")

    def test_hash_is_different_from_original(self):
        """Le hash ne doit pas être le mot de passe en clair."""
        password = "Password123!"
        hashed = hash_password(password)
        assert hashed != password

    def test_same_password_gives_different_hashes(self):
        """bcrypt avec salt aléatoire : deux hashes différents pour le même mot de passe."""
        h1 = hash_password("Password123!")
        h2 = hash_password("Password123!")
        assert h1 != h2

    def test_short_password_raises(self):
        """Un mot de passe trop court doit lever ValueError."""
        with pytest.raises(ValueError, match="8 caractères"):
            hash_password("abc")

    def test_empty_password_raises(self):
        """Un mot de passe vide doit lever ValueError."""
        with pytest.raises(ValueError):
            hash_password("")

    def test_exactly_8_chars_accepted(self):
        """8 caractères exactement doit être accepté."""
        result = hash_password("Abcd123!")
        assert result.startswith("$2b$")


# ── verify_password ───────────────────────────────────────────────────────────

class TestVerifyPassword:
    """Tests pour la vérification de mots de passe."""

    def test_correct_password_returns_true(self):
        """Un mot de passe correct doit retourner True."""
        password = "Password123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_returns_false(self):
        """Un mauvais mot de passe doit retourner False."""
        hashed = hash_password("Password123!")
        assert verify_password("WrongPassword!", hashed) is False

    def test_empty_plain_returns_false(self):
        """Un mot de passe vide en clair doit retourner False sans exception."""
        hashed = hash_password("Password123!")
        assert verify_password("", hashed) is False

    def test_empty_hash_returns_false(self):
        """Un hash vide doit retourner False sans exception."""
        assert verify_password("Password123!", "") is False

    def test_none_values_return_false(self):
        """Des valeurs None doivent retourner False sans exception."""
        assert verify_password(None, None) is False


# ── create_access_token / decode_access_token ─────────────────────────────────

class TestAccessToken:
    """Tests pour les tokens JWT d'accès."""

    def test_token_is_string(self):
        """Le token créé doit être une chaîne."""
        token = create_access_token({"sub": "123"})
        assert isinstance(token, str)

    def test_token_has_three_parts(self):
        """Un JWT valide contient exactement 3 parties séparées par des points."""
        token = create_access_token({"sub": "123"})
        parts = token.split(".")
        assert len(parts) == 3

    def test_decode_valid_token_returns_payload(self):
        """Décoder un token valide doit retourner le payload."""
        token = create_access_token({"sub": "42"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "42"

    def test_decoded_token_has_type_access(self):
        """Le payload décodé doit avoir type='access'."""
        token = create_access_token({"sub": "42"})
        payload = decode_access_token(token)
        assert payload["type"] == "access"

    def test_decoded_token_has_exp(self):
        """Le payload décodé doit contenir une date d'expiration."""
        token = create_access_token({"sub": "42"})
        payload = decode_access_token(token)
        assert "exp" in payload

    def test_invalid_token_returns_none(self):
        """Un token invalide/altéré doit retourner None."""
        assert decode_access_token("not.a.valid.token") is None

    def test_empty_token_returns_none(self):
        """Un token vide doit retourner None."""
        assert decode_access_token("") is None

    def test_wrong_type_token_rejected(self):
        """Un token avec type != 'access' doit être rejeté."""
        from jose import jwt
        from app.config import get_settings
        settings = get_settings()
        # Créer un token avec type='refresh' à la main
        payload = {
            "sub": "42",
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        bad_token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        assert decode_access_token(bad_token) is None

    def test_tampered_token_returns_none(self):
        """Un token dont la signature a été altérée doit retourner None."""
        token = create_access_token({"sub": "42"})
        # Modifier un caractère dans la signature (3ème partie)
        parts = token.split(".")
        parts[2] = parts[2][:-1] + ("A" if parts[2][-1] != "A" else "B")
        tampered = ".".join(parts)
        assert decode_access_token(tampered) is None


# ── create_refresh_token ──────────────────────────────────────────────────────

class TestRefreshToken:
    """Tests pour les tokens de rafraîchissement."""

    def test_refresh_token_is_string(self):
        """Le refresh token doit être une chaîne."""
        token = create_refresh_token()
        assert isinstance(token, str)

    def test_refresh_token_length(self):
        """Le token doit avoir une longueur suffisante (≥ 40 chars en base64url)."""
        token = create_refresh_token()
        assert len(token) >= 40

    def test_refresh_tokens_are_unique(self):
        """Deux refresh tokens générés doivent être différents."""
        t1 = create_refresh_token()
        t2 = create_refresh_token()
        assert t1 != t2

    def test_refresh_token_is_url_safe(self):
        """Le token doit contenir uniquement des caractères URL-safe."""
        import re
        token = create_refresh_token()
        assert re.match(r'^[A-Za-z0-9_\-]+$', token)


# ── create_email_token / decode_email_token ──────────────────────────────────

class TestEmailToken:
    """Tests pour les tokens d'actions email (vérification, reset)."""

    def test_verify_token_decoded_correctly(self):
        """Un token de vérification doit être décodé avec l'email correct."""
        email = "user@example.com"
        token = create_email_token(email, "verify")
        decoded_email = decode_email_token(token, "verify")
        assert decoded_email == email

    def test_reset_token_decoded_correctly(self):
        """Un token de reset doit être décodé avec l'email correct."""
        email = "user@example.com"
        token = create_email_token(email, "reset")
        decoded_email = decode_email_token(token, "reset")
        assert decoded_email == email

    def test_wrong_purpose_returns_none(self):
        """Utiliser un token 'verify' pour un 'reset' doit retourner None."""
        email = "user@example.com"
        verify_token = create_email_token(email, "verify")
        # Essai d'utiliser ce token pour un reset
        assert decode_email_token(verify_token, "reset") is None

    def test_invalid_token_returns_none(self):
        """Un token invalide doit retourner None."""
        assert decode_email_token("invalid.token.here", "verify") is None

    def test_token_contains_email_as_sub(self):
        """Le token JWT doit encoder l'email dans le claim 'sub'."""
        from jose import jwt
        from app.config import get_settings
        settings = get_settings()
        email = "test@example.com"
        token = create_email_token(email, "verify")
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == email
        assert payload["purpose"] == "verify"
