"""
Tests unitaires pour les méthodes des modèles SQLAlchemy.

Ces tests vérifient la logique des modèles sans base de données
(instanciation Python pure, pas de commit en DB).

Couvre :
- User.has_role() — hiérarchie des rôles
- RefreshToken.is_valid() — expiration et révocation
- WaitlistEntry.is_invited() — statut d'invitation
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.models import User, UserRole, RefreshToken, WaitlistEntry


# ── User.has_role() ───────────────────────────────────────────────────────────

class TestUserHasRole:
    """Tests pour la hiérarchie des rôles utilisateur."""

    def _make_user(self, role: UserRole) -> User:
        """Crée un utilisateur en mémoire (sans DB) avec le rôle donné."""
        user = User()
        user.role = role
        return user

    def test_admin_has_all_roles(self):
        """Un admin a accès à tous les niveaux de rôle."""
        admin = self._make_user(UserRole.admin)
        for role in UserRole:
            assert admin.has_role(role), f"Admin doit avoir accès au rôle {role}"

    def test_premium_has_user_and_below(self):
        """Un premium a les rôles premium, user, waitlist, anonymous."""
        premium = self._make_user(UserRole.premium)
        assert premium.has_role(UserRole.premium) is True
        assert premium.has_role(UserRole.user) is True
        assert premium.has_role(UserRole.waitlist) is True
        assert premium.has_role(UserRole.anonymous) is True
        # Mais pas admin
        assert premium.has_role(UserRole.admin) is False

    def test_user_cannot_access_premium_or_admin(self):
        """Un utilisateur standard ne peut pas accéder aux rôles premium/admin."""
        user = self._make_user(UserRole.user)
        assert user.has_role(UserRole.user) is True
        assert user.has_role(UserRole.premium) is False
        assert user.has_role(UserRole.admin) is False

    def test_waitlist_cannot_access_user_plus(self):
        """Un utilisateur waitlist ne peut pas accéder aux rôles user et au-dessus."""
        waitlist = self._make_user(UserRole.waitlist)
        assert waitlist.has_role(UserRole.waitlist) is True
        assert waitlist.has_role(UserRole.anonymous) is True
        assert waitlist.has_role(UserRole.user) is False
        assert waitlist.has_role(UserRole.premium) is False
        assert waitlist.has_role(UserRole.admin) is False

    def test_anonymous_only_has_anonymous(self):
        """Un utilisateur anonyme n'a accès qu'au rôle anonymous."""
        anon = self._make_user(UserRole.anonymous)
        assert anon.has_role(UserRole.anonymous) is True
        assert anon.has_role(UserRole.waitlist) is False
        assert anon.has_role(UserRole.user) is False


# ── RefreshToken.is_valid() ───────────────────────────────────────────────────

class TestRefreshTokenIsValid:
    """Tests pour la validation des tokens de rafraîchissement."""

    def _make_token(self, revoked: bool = False, expires_in_hours: float = 24) -> RefreshToken:
        """Crée un RefreshToken en mémoire avec les paramètres donnés."""
        token = RefreshToken()
        token.revoked = revoked
        token.expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        return token

    def test_valid_token_not_revoked_not_expired(self):
        """Un token non révoqué et non expiré est valide."""
        token = self._make_token(revoked=False, expires_in_hours=24)
        assert token.is_valid() is True

    def test_revoked_token_is_invalid(self):
        """Un token révoqué est invalide même s'il n'est pas expiré."""
        token = self._make_token(revoked=True, expires_in_hours=24)
        assert token.is_valid() is False

    def test_expired_token_is_invalid(self):
        """Un token expiré est invalide même s'il n'est pas révoqué."""
        token = self._make_token(revoked=False, expires_in_hours=-1)
        assert token.is_valid() is False

    def test_revoked_and_expired_is_invalid(self):
        """Un token révoqué ET expiré est invalide."""
        token = self._make_token(revoked=True, expires_in_hours=-1)
        assert token.is_valid() is False

    def test_token_expiring_now_is_valid(self):
        """Un token qui expire dans le futur immédiat est encore valide."""
        token = self._make_token(expires_in_hours=0.001)  # ~3.6 secondes
        assert token.is_valid() is True


# ── WaitlistEntry.is_invited() ────────────────────────────────────────────────

class TestWaitlistEntryIsInvited:
    """Tests pour le statut d'invitation d'une entrée de liste d'attente."""

    def test_not_invited_by_default(self):
        """Une entrée sans invitation ne doit pas être considérée comme invitée."""
        entry = WaitlistEntry()
        entry.invited_at = None
        entry.invitation_token = None
        assert entry.is_invited() is False

    def test_invited_with_token_and_date(self):
        """Une entrée avec token ET date d'invitation est invitée."""
        entry = WaitlistEntry()
        entry.invited_at = datetime.now(timezone.utc)
        entry.invitation_token = "secure-token-123"
        assert entry.is_invited() is True

    def test_token_without_date_not_invited(self):
        """Un token sans date n'est pas suffisant."""
        entry = WaitlistEntry()
        entry.invited_at = None
        entry.invitation_token = "secure-token-123"
        assert entry.is_invited() is False

    def test_date_without_token_not_invited(self):
        """Une date sans token n'est pas suffisante."""
        entry = WaitlistEntry()
        entry.invited_at = datetime.now(timezone.utc)
        entry.invitation_token = None
        assert entry.is_invited() is False


# ── UserRole enum ─────────────────────────────────────────────────────────────

class TestUserRoleEnum:
    """Tests pour l'énumération des rôles."""

    def test_all_expected_roles_exist(self):
        """Tous les rôles attendus doivent exister dans l'enum."""
        expected = {"anonymous", "waitlist", "user", "premium", "admin"}
        actual = {r.value for r in UserRole}
        assert expected == actual

    def test_roles_are_strings(self):
        """Les rôles doivent être des chaînes (UserRole hérite de str)."""
        for role in UserRole:
            assert isinstance(role, str)
            assert isinstance(role.value, str)

    def test_role_comparison(self):
        """La comparaison de rôles doit fonctionner par valeur."""
        assert UserRole.admin == "admin"
        assert UserRole.user != "admin"
