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

### 5. Surveillance de la Sécurité

Le modèle `SecurityEvent` enregistre chaque tentative d'intrusion détectée par le `SecurityMiddleware`. Les événements sont consultables dans le Dashboard Admin.

```python
class SecurityEvent(Base):
    __tablename__ = "security_events"
    event_type  = Column(String, index=True)  # path_scan, injection_attempt…
    severity    = Column(String, index=True)  # low, medium, high, critical
    ip_address  = Column(String, index=True)
    path        = Column(String)
    user_agent  = Column(String)
    details     = Column(JSON)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
```

### 6. Monétisation — Boutique et Abonnements

Deux modèles gèrent la monétisation, activables indépendamment via les variables d'environnement `MONETIZATION_SHOP` et `MONETIZATION_SUBSCRIPTION`.

#### Produits et Achats (`MONETIZATION_SHOP`)

```python
class Product(Base):
    """Produit numérique vendable en une seule fois."""
    __tablename__ = "products"
    name            = Column(String, nullable=False)
    slug            = Column(String, unique=True, index=True)
    price_cents     = Column(Integer, nullable=False)  # 2900 = 29 €
    stripe_price_id = Column(String)   # price_… depuis Stripe Dashboard
    file_path       = Column(String)   # fichier servi de façon sécurisée
    is_active       = Column(Boolean, default=True)

class Purchase(Base):
    """Achat unique — lié à un Product et optionnellement à un User."""
    __tablename__ = "purchases"
    user_id               = Column(Integer, ForeignKey("users.id"))  # nullable (guest)
    product_id            = Column(Integer, ForeignKey("products.id"))
    email                 = Column(String, nullable=False)
    stripe_session_id     = Column(String, unique=True)   # cs_…
    download_token        = Column(String, unique=True)   # token URL sécurisé
    download_count        = Column(Integer, default=0)
    max_downloads         = Column(Integer, default=5)
    token_expires_at      = Column(DateTime(timezone=True))
    fulfilled_at          = Column(DateTime(timezone=True))  # défini par le webhook
```

**Flux de téléchargement sécurisé :**
1. Stripe confirme le paiement via webhook → `fulfilled_at` est défini
2. Un `download_token` unique est généré → envoyé par email
3. `GET /api/shop/download/{token}` vérifie l'expiration et incrémente `download_count`
4. Le fichier est servi directement depuis le serveur (jamais l'URL publique du fichier)

#### Abonnements (`MONETIZATION_SUBSCRIPTION`)

```python
class Subscription(Base):
    """Abonnement Stripe — 1:1 avec User."""
    __tablename__ = "subscriptions"
    user_id                = Column(Integer, ForeignKey("users.id"), unique=True)
    stripe_subscription_id = Column(String, unique=True)  # sub_…
    stripe_customer_id     = Column(String)                # cus_…
    status                 = Column(Enum(SubscriptionStatus))
    current_period_end     = Column(DateTime(timezone=True))
    trial_end              = Column(DateTime(timezone=True))
    cancelled_at           = Column(DateTime(timezone=True))
```

Les statuts possibles : `trialing → active → past_due / cancelled / unpaid`.

La règle métier est simple : si `status in (active, trialing)`, l'utilisateur reçoit le rôle `premium`. Dès que le statut change (non-paiement, annulation), le rôle est automatiquement rétrogradé vers `user`. Cette logique est entièrement gérée par les webhooks Stripe, sans intervention humaine.

## Gestion des Migrations avec Alembic

Dans un projet réel, le schéma de données évolue constamment. **Alembic** est l'outil qui permet de versionner ces changements (ajouter une colonne, créer une table) sans perdre de données.

### Workflow Alembic :
1.  **Générer une migration :** `alembic revision --autogenerate -m "add lang to tutorials"`
2.  **Vérifier le script généré :** Dans `alembic/versions/`.
3.  **Appliquer :** `alembic upgrade head`

C'est ce processus qui garantit que votre base de données en production reste synchronisée avec votre code source.

---

*Le schéma étant posé, nous allons maintenant voir comment exposer ces données via une API performante dans le chapitre suivant.*
