"""
Module de gestion de la sécurité : hachage de mots de passe et tokens JWT.

Ce module fournit les fonctions essentielles pour :
- Le hachage et la vérification des mots de passe (bcrypt)
- La création et validation des tokens d'accès JWT
- La gestion des tokens de rafraîchissement opaques (sécurisés)
- Les tokens signés pour les emails (vérification, reset password)
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

# Chargement de la configuration
settings = get_settings()

# Contexte de hachage bcrypt configuré pour le hachage de mots de passe
# "auto" permettra la migration vers de futurs algorithmes si nécessaire
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Coût computationnel (12 est un bon équilibre sécurité/perf)
)


def hash_password(password: str) -> str:
    """
    Hache un mot de passe en clair avec bcrypt.
    
    Args:
        password: Mot de passe en clair (sera salé automatiquement)
        
    Returns:
        str: Hash bcrypt du mot de passe (format modulaire : $2b$12$...)
        
    Raises:
        ValueError: Si le mot de passe est vide ou trop court
        
    Example:
        >>> hash = hash_password("my_secure_password")
        >>> hash.startswith('$2b$')
        True
    """
    if not password or len(password) < 8:
        raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond à un hash.
    
    Cette fonction est résistante aux attaques par timing (constant-time).
    
    Args:
        plain: Mot de passe en clair à vérifier
        hashed: Hash stocké en base de données
        
    Returns:
        bool: True si le mot de passe correspond, False sinon
        
    Example:
        >>> verify_password("wrong", hash)
        False
        >>> verify_password("correct", hash)
        True
    """
    if not plain or not hashed:
        return False
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    """
    Crée un token d'accès JWT signé.
    
    Ce token est utilisé pour l'authentification des requêtes API.
    Il a une durée de vie courte (15 minutes par défaut).
    
    Args:
        data: Dictionnaire contenant les claims (typiquement {"sub": user_id})
        
    Returns:
        str: Token JWT encodé (header.payload.signature)
        
    Note:
        Le token inclut automatiquement :
        - exp: Date d'expiration
        - type: "access" pour différencier des autres types de tokens
        - iat: Date de création (ajoutée automatiquement par jose)
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc)
    })
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm
    )


def create_refresh_token() -> str:
    """
    Génère un token de rafraîchissement opaque cryptographiquement sécurisé.
    
    Contrairement aux tokens d'accès, les refresh tokens ne sont PAS des JWT.
    Ils sont stockés en base de données (hashés) et permettent :
    - L'invalidation côté serveur (révocation)
    - La rotation des tokens (sécurité accrue)
    - La détection de vol (si réutilisation d'un token révoqué)
    
    Returns:
        str: Token aléatoire URL-safe de 64 caractères (512 bits d'entropie)
        
    Security:
        - 64 octets = 512 bits d'entropie (très résistant à la force brute)
        - Généré avec secrets.token_urlsafe (CSPRNG)
        - Doit être hashé (SHA-256) avant stockage en base
    """
    return secrets.token_urlsafe(64)


def decode_access_token(token: str) -> dict | None:
    """
    Décode et valide un token d'accès JWT.
    
    Vérifie la signature, l'expiration et le type de token.
    
    Args:
        token: Token JWT complet (string)
        
    Returns:
        dict: Payload décodé si valide, None sinon
        
    Returns None si:
        - Signature invalide
        - Token expiré
        - Type incorrect (pas un token d'accès)
        - Format malformé
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        # Vérification du type pour éviter la confusion de tokens
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        # JWTError couvre : ExpiredSignatureError, JWTClaimsError, etc.
        return None


def create_email_token(email: str, purpose: Literal["verify", "reset"]) -> str:
    """
    Crée un token signé pour les actions email (vérification, reset MDP).
    
    Ces tokens sont envoyés par email et permettent de valider une action
    spécifique sans authentification préalable.
    
    Args:
        email: Adresse email concernée (sera le subject du token)
        purpose: But du token ("verify" ou "reset")
        
    Returns:
        str: Token JWT avec durée de vie de 24 heures
        
    Security:
        - Durée courte (24h) pour limiter la fenêtre d'attaque
        - Purpose binding: le token ne peut être utilisé que pour l'action prévue
        - Single-use: doit être invalidé après utilisation côté serveur
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {
        "sub": email,
        "purpose": purpose,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm
    )


def decode_email_token(token: str, purpose: Literal["verify", "reset"]) -> str | None:
    """
    Décode et valide un token email.
    
    Vérifie que le token est valide ET qu'il correspond au but attendu
    (vérification d'email ou reset de mot de passe).
    
    Args:
        token: Token JWT reçu par email
        purpose: But attendu ("verify" ou "reset")
        
    Returns:
        str: Email extrait du token si valide, None sinon
        
    Returns None si:
        - Token expiré ou signature invalide
        - Purpose ne correspond pas (tentative de réutilisation)
        - Email manquant dans le payload
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        # Vérification stricte du purpose (security: pas de confusion possible)
        if payload.get("purpose") != purpose:
            return None
        return payload.get("sub")
    except JWTError:
        return None