"""
Factories de données de test avec factory-boy.

Permet de créer rapidement des objets de test cohérents
avec des valeurs par défaut sensées et personnalisables.

Usage :
    # Créer un utilisateur avec les valeurs par défaut
    user = UserFactory()

    # Surcharger des attributs
    admin = UserFactory(role=UserRole.admin, is_verified=True)

    # Créer sans persister en DB
    user_dict = UserFactory.build().__dict__
"""

import factory
from factory import Faker
from faker import Faker as FakerLib

from app.models import User, UserRole, WaitlistEntry, Tutorial, Lesson, AccessRole
from app.auth.security import hash_password

fake = FakerLib("fr_FR")


class UserFactory(factory.Factory):
    """Factory pour créer des utilisateurs de test."""

    class Meta:
        model = User

    email = factory.LazyFunction(lambda: fake.unique.email())
    hashed_password = factory.LazyFunction(lambda: hash_password("Password123!"))
    full_name = factory.LazyFunction(lambda: fake.name())
    role = UserRole.user
    is_active = True
    is_verified = True

    class Params:
        """Paramètres de raccourci pour les rôles courants."""

        admin = factory.Trait(
            role=UserRole.admin,
            email=factory.LazyFunction(lambda: f"admin_{fake.unique.random_int()}@test.com"),
            is_verified=True,
        )
        premium = factory.Trait(
            role=UserRole.premium,
            is_verified=True,
        )
        waitlist = factory.Trait(
            role=UserRole.waitlist,
            is_verified=False,
        )
        unverified = factory.Trait(
            is_verified=False,
        )
        inactive = factory.Trait(
            is_active=False,
        )


class WaitlistEntryFactory(factory.Factory):
    """Factory pour les entrées de liste d'attente."""

    class Meta:
        model = WaitlistEntry

    email = factory.LazyFunction(lambda: fake.unique.email())


class TutorialFactory(factory.Factory):
    """Factory pour les tutorials de test."""

    class Meta:
        model = Tutorial

    title = factory.LazyFunction(lambda: fake.sentence(nb_words=4).rstrip("."))
    slug = factory.LazyFunction(lambda: fake.slug())
    description = factory.LazyFunction(lambda: fake.paragraph())
    access_role = AccessRole.user
    is_published = True
    lang = "fr"
    author_id = None

    class Params:
        premium = factory.Trait(access_role=AccessRole.premium)
        draft = factory.Trait(is_published=False)


class LessonFactory(factory.Factory):
    """Factory pour les leçons de test."""

    class Meta:
        model = Lesson

    title = factory.LazyFunction(lambda: fake.sentence(nb_words=5).rstrip("."))
    slug = factory.LazyFunction(lambda: fake.slug())
    order = factory.Sequence(lambda n: n)
    content = factory.LazyFunction(lambda: f"# Titre\n\n{fake.paragraph()}")
    duration_minutes = factory.LazyFunction(lambda: fake.random_int(min=5, max=60))
    is_published = True
    tutorial_id = None


# ── Helpers de construction rapide ───────────────────────────────────────────

def make_register_payload(
    email: str | None = None,
    password: str = "Password123!",
    full_name: str | None = None,
) -> dict:
    """Génère un payload valide pour POST /api/auth/register."""
    return {
        "email": email or fake.unique.email(),
        "password": password,
        "full_name": full_name or fake.name(),
    }


def make_login_payload(email: str, password: str = "Password123!") -> dict:
    """Génère un payload valide pour POST /api/auth/login."""
    return {
        "email": email,
        "password": password,
    }
