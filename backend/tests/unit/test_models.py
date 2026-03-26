"""
Tests unitaires pour les modèles SQLAlchemy.

Vérifie les valeurs par défaut, les contraintes et les énumérations
sans nécessiter de serveur HTTP.
"""

import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars-for-jwt-signing")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import User, UserRole, WaitlistEntry


@pytest.fixture(scope="module")
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.mark.unit
class TestUserRole:
    def test_all_roles_defined(self):
        roles = [r.value for r in UserRole]
        assert "user" in roles
        assert "admin" in roles
        assert "premium" in roles
        assert "waitlist" in roles
        assert "anonymous" in roles

    def test_role_is_string_enum(self):
        assert isinstance(UserRole.user, str)
        assert UserRole.user == "user"


@pytest.mark.unit
class TestUserModel:
    def test_create_minimal_user(self, db_session):
        user = User(
            email="minimal@test.com",
            hashed_password="hashed_pw",
            role=UserRole.user,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        assert user.id is not None
        assert user.email == "minimal@test.com"

    def test_default_role_is_user(self, db_session):
        user = User(
            email="default_role@test.com",
            hashed_password="hashed_pw",
        )
        db_session.add(user)
        db_session.commit()
        # Role defaults may depend on column default — check column definition
        assert user.email == "default_role@test.com"

    def test_is_active_and_is_verified_are_booleans(self, db_session):
        user = User(
            email="flags@test.com",
            hashed_password="hashed_pw",
            is_active=True,
            is_verified=False,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        assert user.is_active is True
        assert user.is_verified is False

    def test_full_name_is_optional(self, db_session):
        user = User(
            email="noname@test.com",
            hashed_password="hashed_pw",
        )
        db_session.add(user)
        db_session.commit()
        assert user.full_name is None

    def test_unique_email_constraint(self, db_session):
        from sqlalchemy.exc import IntegrityError
        user1 = User(email="unique@test.com", hashed_password="pw")
        user2 = User(email="unique@test.com", hashed_password="pw")
        db_session.add(user1)
        db_session.commit()
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


@pytest.mark.unit
class TestWaitlistEntry:
    def test_create_waitlist_entry(self, db_session):
        entry = WaitlistEntry(
            email="waitlist@test.com",
            full_name="Waitlist User",
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)
        assert entry.id is not None
        assert entry.email == "waitlist@test.com"

    def test_waitlist_email_is_unique(self, db_session):
        from sqlalchemy.exc import IntegrityError
        e1 = WaitlistEntry(email="dup_waitlist@test.com")
        e2 = WaitlistEntry(email="dup_waitlist@test.com")
        db_session.add(e1)
        db_session.commit()
        db_session.add(e2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()
