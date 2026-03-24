"""
Module de configuration et de gestion de la connexion à la base de données.

Ce module initialise :
- Le moteur SQLAlchemy (engine)
- La fabrique de sessions (sessionmaker)
- La classe de base déclarative pour les modèles
- Le gestionnaire de dépendance FastAPI pour l'injection de sessions
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool


# Récupération de l'URL de connexion depuis les variables d'environnement
# Format attendu : postgresql://user:password@host:port/database
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "La variable d'environnement DATABASE_URL doit être définie. "
        "Exemple: postgresql://user:password@localhost:5432/dbname"
    )

# Création du moteur de connexion à la base de données
# pool_pre_ping=True vérifie la validité des connexions avant utilisation
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Vérifie que la connexion est vivante avant utilisation
    echo=False           # Mettre à True pour déboguer les requêtes SQL
)

# Fabrique de sessions configurée pour une utilisation avec FastAPI
# autocommit=False : les transactions doivent être explicitement commitées
# autoflush=False : évite les requêtes implicites avant chaque requête
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    """
    Classe de base déclarative pour tous les modèles SQLAlchemy.
    
    Tous les modèles ORM doivent hériter de cette classe pour bénéficier
    de la introspection et du mapping automatique.
    """
    pass


def get_db():
    """
    Générateur de session de base de données pour FastAPI Depends.
    
    Cette fonction est utilisée comme dépendance FastAPI pour injecter
    une session de base de données dans les endpoints. Elle garantit
    la fermeture automatique de la session même en cas d'exception.
    
    Yields:
        Session: Session SQLAlchemy active et configurée
        
    Example:
        >>> @app.get("/items")
        ... async def read_items(db: Session = Depends(get_db)):
        ...     return db.query(Item).all()
        
    Note:
        La session est automatiquement fermée grâce au bloc try/finally,
        évitant ainsi les fuites de connexions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()