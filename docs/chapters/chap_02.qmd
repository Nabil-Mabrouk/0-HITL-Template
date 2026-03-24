---
title: "Initialisation du Backend avec FastAPI"
---

## Pourquoi FastAPI ?

Pour le projet **0-HITL**, nous avons besoin d'un backend capable de gérer des tâches asynchrones, une validation de données stricte et une documentation automatique. FastAPI s'est imposé comme le choix naturel grâce à :

1.  **Performance :** Basé sur Starlette et Pydantic, il est l'un des frameworks Python les plus rapides.
2.  **Asynchronisme natif :** Crucial pour les appels à l'IA ou les traitements de données lourds sans bloquer l'API.
3.  **Type Safety :** Utilisation intensive des hints Python pour réduire les bugs et améliorer l'auto-complétion.

## Structure d'un Projet Professionnel

Une application backend doit être organisée pour rester maintenable à mesure qu'elle grandit. Voici la structure adoptée pour 0-HITL :

```text
backend/
├── app/
│   ├── auth/           # Sécurité et dépendances JWT
│   ├── email/          # Services d'envoi d'emails (templates jinja2)
│   ├── geoip/          # Service de géolocalisation IP
│   ├── middleware/     # Tracking et gestion des requêtes
│   ├── onboarding/     # Moteur de profilage dynamique
│   ├── routers/        # Points d'entrée de l'API (endpoints)
│   ├── schemas/        # Validation Pydantic (Input/Output)
│   ├── config.py       # Paramètres via Pydantic Settings
│   ├── database.py     # Session et moteur SQLAlchemy
│   ├── main.py         # Initialisation FastAPI
│   └── models.py       # Définition des tables SQL
├── alembic/            # Scripts de migration
├── uploads/            # Stockage des médias
├── requirements.txt    # Dépendances Python
└── alembic.ini         # Configuration des migrations
```

## Configuration Centralisée avec Pydantic Settings

Nous utilisons `pydantic-settings` pour charger et valider nos variables d'environnement. Cela garantit que si une variable cruciale (comme `SECRET_KEY`) est manquante, l'application refuse de démarrer.

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    frontend_url: str = "http://localhost:5173"
    environment: str = "development"
    
    # PostgreSQL
    database_url: str
    
    # Auth configuration
    auth_channel_waitlist: bool = True
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

## Connexion à la Base de Données (SQLAlchemy)

Pour 0-HITL, nous utilisons **SQLAlchemy** comme ORM (Object-Relational Mapper). La connexion est gérée via un pattern de "Dependency Injection" pour fournir une session fraîche à chaque requête.

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Création du moteur
engine = create_engine(settings.database_url)

# Fabrique de sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour nos modèles
Base = declarative_base()

# Dépendance pour FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Le Point d'Entrée : `main.py`

Le fichier `main.py` orchestre l'application, les middlewares (CORS, Tracking) et inclut les différents routeurs.

```python
# app/main.py
from fastapi import FastAPI
from app.routers import auth, users, content

app = FastAPI(title="0-HITL API")

# Configuration CORS pour autoriser le Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des modules de l'API
app.include_router(auth.router, prefix="/api/auth")
app.include_router(content.router, prefix="/api/content")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

## Lancer le Backend

Grâce à Docker Compose, le lancement est automatique. Cependant, il est utile de savoir comment Uvicorn démarre le serveur en coulisses :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Le flag `--reload` permet de redémarrer le serveur à chaque fois qu'un fichier est modifié, ce qui est indispensable en phase de développement.

---

*Dans le chapitre suivant, nous allons concevoir notre schéma de données pour modéliser les utilisateurs, les parcours d'apprentissage et le tracking des visites.*
