"""
Configuration globale de pytest pour tous les tests backend.

Ce fichier est chargé automatiquement par pytest avant l'exécution des tests.
Il configure :
- La base de données SQLite en mémoire (isolation complète)
- L'override des dépendances FastAPI
- Les fixtures partagées (client HTTP, session DB, utilisateurs de test)
"""

import os

# ── Variables d'environnement avant tout import de l'app ─────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars-for-jwt-signing")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("ADMIN_PASSWORD", "AdminTest123!")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.auth.security import hash_password
from app.models import User, UserRole, WaitlistEntry

# ── Configuration de la base de données de test ───────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite://"  # En mémoire, isolation maximale

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Partage la même connexion entre les threads
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_settings():
    """Force le rechargement des settings avec les variables de test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="function")
def db():
    """
    Session de base de données isolée pour chaque test.

    Crée et détruit les tables à chaque test pour une isolation totale.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Client HTTP FastAPI avec override de la dépendance base de données.

    Injecte la session de test à la place de la session de production.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ── Fixtures utilisateurs ─────────────────────────────────────────────────────

@pytest.fixture
def regular_user(db) -> User:
    """Crée un utilisateur standard vérifié."""
    user = User(
        email="user@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Test User",
        role=UserRole.user,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db) -> User:
    """Crée un utilisateur administrateur."""
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Admin User",
        role=UserRole.admin,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def premium_user(db) -> User:
    """Crée un utilisateur premium."""
    user = User(
        email="premium@test.com",
        hashed_password=hash_password("Premium123!"),
        full_name="Premium User",
        role=UserRole.premium,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def waitlist_entry(db) -> WaitlistEntry:
    """Crée une entrée en liste d'attente."""
    entry = WaitlistEntry(
        email="waiting@test.com",
        full_name="Waiting User",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ── Fixtures tokens ───────────────────────────────────────────────────────────

@pytest.fixture
def user_token(client, regular_user) -> str:
    """Retourne un token d'accès valide pour l'utilisateur standard."""
    resp = client.post("/auth/login", json={
        "email": regular_user.email,
        "password": "Password123!",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user) -> str:
    """Retourne un token d'accès valide pour l'administrateur."""
    resp = client.post("/auth/login", json={
        "email": admin_user.email,
        "password": "AdminPass123!",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]
