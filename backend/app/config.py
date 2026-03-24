"""
Module de configuration centralisée de l'application.

Utilise Pydantic Settings pour charger les variables d'environnement
avec validation des types et valeurs par défaut. Le pattern singleton
via `lru_cache` garantit une seule instance des settings en mémoire.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Configuration de l'application chargée depuis les variables d'environnement.
    
    Cette classe centralise tous les paramètres configurables de l'application
    avec des valeurs par défaut sensibles pour le développement local.
    
    Les variables sont chargées depuis :
    1. Les variables d'environnement système
    2. Le fichier .env (si présent)
    
    Attributes:
        # JWT
        secret_key: Clé secrète pour signer les tokens (REQUIRED)
        access_token_expire_minutes: Durée de validité des tokens d'accès
        refresh_token_expire_days: Durée de validité des tokens de rafraîchissement
        algorithm: Algorithme de signature JWT
        
        # SMTP
        smtp_host: Serveur SMTP pour l'envoi d'emails
        smtp_port: Port du serveur SMTP
        smtp_user: Nom d'utilisateur SMTP
        smtp_password: Mot de passe SMTP
        email_from: Adresse d'expédition des emails
        email_from_name: Nom d'affichage de l'expéditeur
        
        # App
        frontend_url: URL du frontend pour les liens dans les emails
        environment: Environnement d'exécution (development/staging/production)
    """
    
    # ==================== JWT Configuration ====================
    secret_key: str
    """
    Clé secrète pour la signature des tokens JWT.
    
    WARNING: Doit être une chaîne aléatoire forte en production (min 256 bits).
    Utiliser: openssl rand -hex 32
    """
    
    access_token_expire_minutes: int = 15
    """Durée de validité des tokens d'accès JWT en minutes (courte durée)."""
    
    refresh_token_expire_days: int = 7
    """Durée de validité des tokens de rafraîchissement en jours."""
    
    algorithm: str = "HS256"
    """
    Algorithme de signature JWT.
    
    Options recommandées:
    - HS256: HMAC avec SHA-256 (symétrique, plus rapide)
    - RS256: RSA avec SHA-256 (asymétrique, meilleur pour microservices)
    """
    
    # ==================== SMTP Configuration ====================
    smtp_host: str = "smtp.gmail.com"
    """Hôte du serveur SMTP (défaut: Gmail)."""
    
    smtp_port: int = 587
    """
    Port SMTP.
    
    587: TLS (recommandé)
    465: SSL (legacy)
    25: Non sécurisé (déconseillé)
    """
    
    smtp_user: str = ""
    """Nom d'utilisateur pour l'authentification SMTP."""
    
    smtp_password: str = ""
    """
    Mot de passe ou token d'application pour SMTP.
    
    SECURITY: Ne jamais commiter de vraies credentials.
    Utiliser des variables d'environnement ou des secrets managers.
    """
    
    email_from: str = ""
    """Adresse email d'expédition (doit correspondre à smtp_user sur Gmail)."""
    
    email_from_name: str = "0-HITL"
    """Nom d'affichage de l'expéditeur dans les clients mail."""
    
    # ==================== Application Configuration ====================
    frontend_url: str = "http://localhost:5173"
    """
    URL de base du frontend.
    
    Utilisée pour générer les liens dans les emails (confirmation, reset MDP).
    Doit correspondre à l'origine CORS autorisée.
    """
    
    environment: str = "development"
    """
    Environnement d'exécution de l'application.
    
    Valeurs possibles:
    - development: Debug activé, logs verbeux, erreurs détaillées
    - staging: Pré-production, données de test
    - production: Optimisé, logs minimaux, erreurs masquées
    """

    # ==================== Auth Configuration ====================

    # Canaux d'authentification
    auth_channel_waitlist:   bool = True
    auth_channel_direct:     bool = False
    auth_channel_onboarding: bool = False


    # ==================== Auth Configuration ====================
    # Onboarding
    auth_onboarding_flow:        str = "default"
    auth_onboarding_target_role: str = "premium"
    
    # ==================== Geolocalisation ====================
    geoip_db_path: str = "./geoip/GeoLite2-City.mmdb"

    # ==================== SEO Configuration ====================
    robots_allow_indexing: bool = True
    robots_disallow_paths: str  = "/admin,/profile,/api"

    # ==================== Admin Configuration ====================
    admin_email:     str = ""
    admin_password:  str = ""
    admin_full_name: str = "Admin"

    class Config:
        """Configuration interne de Pydantic Settings."""
        
        env_file = ".env"
        """Nom du fichier d'environnement à charger."""
        
        case_sensitive = False
        """
        Les variables d'environnement sont insensibles à la casse.
        
        Exemple: SECRET_KEY et secret_key sont équivalents.
        """
        
        env_file_encoding = "utf-8"
        """Encodage du fichier .env."""


@lru_cache()
def get_settings() -> Settings:
    """
    Retourne l'instance unique des paramètres de configuration.
    
    Cette fonction utilise `lru_cache` pour implémenter le pattern Singleton,
    garantissant qu'une seule instance de Settings est créée et réutilisée
    dans toute l'application. Cela évite les rechargements multiples du fichier
    .env et améliore les performances.
    
    Returns:
        Settings: Instance unique et mise en cache des paramètres
        
    Example:
        >>> from app.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.frontend_url)
        'http://localhost:5173'
        
    Note:
        En cas de modification du fichier .env, un redémarrage de l'application
        est nécessaire pour prendre en compte les changements.
    """
    return Settings()