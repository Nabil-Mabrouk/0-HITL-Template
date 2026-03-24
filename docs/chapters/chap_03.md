# Modélisation des Données avec SQLAlchemy

## Introduction à la Modélisation

Le schéma de données est la colonne vertébrale du projet **0-HITL**. Nous utilisons **SQLAlchemy**, l'ORM (Object-Relational Mapper) le plus puissant de l'écosystème Python, pour définir nos tables sous forme de classes Python.

Cette approche nous permet de :
1.  Bénéficier d'une validation de type forte.
2.  Manipuler des objets Python plutôt que d'écrire du SQL brut.
3.  Garantir l'intégrité référentielle entre les différentes entités.

## Les Entités Cœurs de 0-HITL

Notre application s'articule autour de quatre domaines principaux : les utilisateurs, l'authentification, le contenu pédagogique et l'analytique.

### 1. Gestion des Utilisateurs et Rôles

Le modèle `User` centralise l'identité et les permissions. Nous utilisons une énumération (`UserRole`) pour hiérarchiser les accès :

```python
class UserRole(str, enum.Enum):
    anonymous = "anonymous"
    waitlist  = "waitlist"
    user      = "user"
    premium   = "premium"
    admin     = "admin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user)
    is_active = Column(Boolean, default=True)
```

### 2. Contenu Pédagogique : Tutoriaux et Leçons

L'université virtuelle repose sur une relation **One-to-Many** entre `Tutorial` et `Lesson`. Un tutorial est un conteneur de leçons ordonnées.

```python
class Tutorial(Base):
    __tablename__ = "tutorials"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True)
    lang = Column(String(5), default="fr", index=True)
    access_role = Column(Enum(AccessRole), default=AccessRole.user)
    
    lessons = relationship("Lesson", back_populates="tutorial", order_by="Lesson.order")

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True)
    tutorial_id = Column(Integer, ForeignKey("tutorials.id", ondelete="CASCADE"))
    title = Column(String, nullable=False)
    content = Column(Text) # Stockage Markdown
    order = Column(Integer, default=0)
```

### 3. Profilage Dynamique (Onboarding)

Le modèle `UserProfile` stocke les résultats du questionnaire d'onboarding. Il est lié de manière **1:1** à l'utilisateur.

```python
class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    flow_id = Column(String, nullable=False)
    answers = Column(Text) # JSON sérialisé des réponses
    profile = Column(String) # Label calculé (ex: 'power_user')
    score   = Column(Integer)
```

### 4. Analytique RGPD-friendly

Le modèle `Visit` enregistre l'activité sur la plateforme. Pour respecter la vie privée, nous ne stockons jamais l'IP en clair, mais un hash anonymisé.

```python
class Visit(Base):
    __tablename__ = "visits"
    ip_hash = Column(String, index=True)
    country_code = Column(String(2), index=True)
    city = Column(String)
    path = Column(String) # URL visitée
    user_role = Column(String) # Contexte au moment de la visite
```

## Gestion des Migrations avec Alembic

Dans un projet réel, le schéma de données évolue constamment. **Alembic** est l'outil qui permet de versionner ces changements (ajouter une colonne, créer une table) sans perdre de données.

### Workflow Alembic :
1.  **Générer une migration :** `alembic revision --autogenerate -m "add lang to tutorials"`
2.  **Vérifier le script généré :** Dans `alembic/versions/`.
3.  **Appliquer :** `alembic upgrade head`

C'est ce processus qui garantit que votre base de données en production reste synchronisée avec votre code source.

---

*Le schéma étant posé, nous allons maintenant voir comment exposer ces données via une API performante dans le chapitre suivant.*
