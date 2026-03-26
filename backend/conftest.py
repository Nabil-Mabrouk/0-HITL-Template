"""
Configuration globale des tests pytest pour Z-HITL.

Ce fichier définit les fixtures partagées entre tous les tests :
- Base de données SQLite en mémoire (isolée par test)
- Client HTTP (TestClient httpx)
- Utilisateurs préconstruits avec différents rôles
- Tokens JWT prêts à l'emploi

Architecture de test :
    conftest.py         ← ce fichier (fixtures globales)
    tests/
    ├── factories.py    ← constructeurs de données de test
    ├── unit/           ← tests sans base de données
    └── integration/    ← tests avec base de données + API
"""

import os
import pytest
from datetime import datetime, timezone, timedelta
from typing import Generator

# ── Variables d'environnement de test ─────────────────────────────────────────
# Doit être fait AVANT tout import de l'application
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars-for-jwt-signing")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("ADMIN_PASSWORD", "AdminTest123!")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_PORT", "587")
os.environ.setdefault("SMTP_USER", "test@test.com")
os.environ.setdefault("SMTP_PASSWORD", "test")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole, WaitlistEntry, Tutorial, Lesson, AccessRole
from app.auth.security import hash_password, create_access_token

# ── Base de données SQLite en mémoire ────────────────────────────────────────
# Utilise SQLite pour les tests — aucune dépendance PostgreSQL nécessaire.
# Chaque session de test repart d'une base propre.

SQLALCHEMY_TEST_URL = "sqlite:///./test_db.sqlite"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},  # Requis pour SQLite + threading
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    """Crée toutes les tables au début de la session de test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Nettoyer le fichier SQLite
    import os
    if os.path.exists("test_db.sqlite"):
        os.remove("test_db.sqlite")


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Session de base de données isolée pour chaque test.

    Utilise une transaction annulée après chaque test pour garantir
    l'isolation complète entre les tests.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Client HTTP de test avec base de données injectée.

    Remplace la dépendance get_db de FastAPI par la session de test,
    garantissant que les requêtes API utilisent la même transaction.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass  # La session est gérée par la fixture db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ── Fixtures utilisateurs ────────────────────────────────────────────────────

@pytest.fixture
def user_anonymous(db: Session) -> User:
    """Utilisateur non connecté (role anonymous)."""
    user = User(
        email="anonymous@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Anonymous User",
        role=UserRole.anonymous,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_waitlist(db: Session) -> User:
    """Utilisateur en liste d'attente."""
    user = User(
        email="waitlist@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Waitlist User",
        role=UserRole.waitlist,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_standard(db: Session) -> User:
    """Utilisateur standard vérifié (role user)."""
    user = User(
        email="user@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Standard User",
        role=UserRole.user,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_premium(db: Session) -> User:
    """Utilisateur premium vérifié."""
    user = User(
        email="premium@test.com",
        hashed_password=hash_password("Password123!"),
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
def user_admin(db: Session) -> User:
    """Administrateur vérifié."""
    user = User(
        email="admin@test.com",
        hashed_password=hash_password("Password123!"),
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
def user_inactive(db: Session) -> User:
    """Utilisateur désactivé (banni)."""
    user = User(
        email="inactive@test.com",
        hashed_password=hash_password("Password123!"),
        full_name="Inactive User",
        role=UserRole.user,
        is_active=False,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Fixtures tokens JWT ──────────────────────────────────────────────────────

@pytest.fixture
def token_user(user_standard: User) -> str:
    """Token JWT valide pour un utilisateur standard."""
    return create_access_token({"sub": str(user_standard.id)})


@pytest.fixture
def token_premium(user_premium: User) -> str:
    """Token JWT valide pour un utilisateur premium."""
    return create_access_token({"sub": str(user_premium.id)})


@pytest.fixture
def token_admin(user_admin: User) -> str:
    """Token JWT valide pour un administrateur."""
    return create_access_token({"sub": str(user_admin.id)})


@pytest.fixture
def auth_headers_user(token_user: str) -> dict:
    """Headers HTTP avec token Bearer pour un utilisateur standard."""
    return {"Authorization": f"Bearer {token_user}"}


@pytest.fixture
def auth_headers_premium(token_premium: str) -> dict:
    """Headers HTTP avec token Bearer pour un utilisateur premium."""
    return {"Authorization": f"Bearer {token_premium}"}


@pytest.fixture
def auth_headers_admin(token_admin: str) -> dict:
    """Headers HTTP avec token Bearer pour un administrateur."""
    return {"Authorization": f"Bearer {token_admin}"}


# ── Fixtures contenu ─────────────────────────────────────────────────────────

@pytest.fixture
def tutorial_free(db: Session, user_admin: User) -> Tutorial:
    """Tutorial libre (accès user) publié."""
    tutorial = Tutorial(
        title="Introduction à Python",
        slug="intro-python",
        description="Apprenez Python de zéro",
        access_role=AccessRole.user,
        is_published=True,
        lang="fr",
        author_id=user_admin.id,
    )
    db.add(tutorial)
    db.commit()
    db.refresh(tutorial)
    return tutorial


@pytest.fixture
def tutorial_premium(db: Session, user_admin: User) -> Tutorial:
    """Tutorial premium (accès réservé) publié."""
    tutorial = Tutorial(
        title="Python Avancé",
        slug="python-avance",
        description="Techniques avancées Python",
        access_role=AccessRole.premium,
        is_published=True,
        lang="fr",
        author_id=user_admin.id,
    )
    db.add(tutorial)
    db.commit()
    db.refresh(tutorial)
    return tutorial


@pytest.fixture
def lesson(db: Session, tutorial_free: Tutorial) -> Lesson:
    """Leçon publiée dans un tutorial libre."""
    lesson = Lesson(
        tutorial_id=tutorial_free.id,
        title="Leçon 1 : Variables",
        slug="variables",
        order=1,
        content="# Variables\n\nEn Python, une variable se déclare ainsi...",
        duration_minutes=10,
        is_published=True,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson
