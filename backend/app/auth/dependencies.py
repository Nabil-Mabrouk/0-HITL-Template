"""
Module de dépendances FastAPI pour l'authentification et l'autorisation.

Ce module fournit des dépendances réutilisables pour sécuriser les endpoints :
- Extraction et validation du token Bearer
- Récupération de l'utilisateur courant
- Vérification de l'état du compte (actif, vérifié)
- Contrôle d'accès basé sur les rôles (RBAC)
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.auth.security import decode_access_token

# Schéma de sécurité HTTP Bearer pour l'extraction du token
# auto_error=False permet de gérer manuellement l'erreur si token manquant
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dépendance qui extrait et valide l'utilisateur depuis le token JWT.
    
    Cette dépendance est la base de toute protection d'endpoint. Elle :
    1. Extrait le token du header Authorization
    2. Décode et valide le token JWT
    3. Récupère l'utilisateur en base de données
    4. Vérifie que le compte est actif
    
    Args:
        credentials: Credentials extraits du header Authorization (Bearer token)
        db: Session de base de données injectée
        
    Returns:
        User: Instance de l'utilisateur authentifié et actif
        
    Raises:
        HTTPException: 401 si token manquant, invalide, ou utilisateur inactif
        
    Example:
        >>> @app.get("/profile")
        ... async def profile(user: User = Depends(get_current_user)):
        ...     return {"email": user.email}
    """
    # Vérification de la présence du token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification manquant",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Décodage et validation du token JWT
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Récupération de l'utilisateur en base
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformé (subject manquant)"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    # Vérifications de sécurité
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte désactivé"
        )
    
    # Injecter dans le state pour le tracking middleware
    request.state.user_id   = user.id
    request.state.user_role = user.role.value
    
    return user


def get_verified_user(user: User = Depends(get_current_user)) -> User:
    """
    Dépendance qui étend get_current_user avec vérification de l'email.
    
    Utilisée pour les endpoints nécessitant un compte confirmé (ex: transactions).
    
    Args:
        user: Utilisateur déjà authentifié via get_current_user
        
    Returns:
        User: Utilisateur avec email vérifié
        
    Raises:
        HTTPException: 403 si l'email n'a pas été confirmé
        
    Note:
        Cette dépendance empile get_current_user, donc elle hérite aussi
        de toutes les vérifications de token et de compte actif.
    """
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email non vérifié. Veuillez confirmer votre adresse email."
        )
    return user


def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """
    Dépendance optionnelle pour l'authentification.
    Retourne l'utilisateur si le token est valide, sinon None.
    Ne lève JAMAIS d'exception 401.
    """
    if not credentials:
        return None
    
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None
    
    # Injecter dans le state pour le tracking middleware
    request.state.user_id   = user.id
    request.state.user_role = user.role.value
    
    return user


def require_role(*roles: UserRole):
    """
    Fabrique de dépendances pour la vérification des rôles (RBAC).
    
    Permet de créer des dépendances personnalisées en spécifiant les rôles
    autorisés. Supporte la vérification d'email implicite via get_verified_user.
    
    Args:
        *roles: Liste des rôles autorisés pour l'endpoint
        
    Returns:
        Callable: Fonction de dépendance configurée pour les rôles spécifiés
        
    Example:
        >>> # Endpoint accessible uniquement aux admins
        >>> @app.delete("/users/{id}")
        ... async def delete_user(
        ...     user: User = Depends(require_role(UserRole.admin))
        ... ):
        ...     pass
        
        >>> # Endpoint accessible aux users et premium
        >>> @app.get("/content")
        ... async def get_content(
        ...     user: User = Depends(require_role(UserRole.user, UserRole.premium))
        ... ):
        ...     pass
    """
    def checker(user: User = Depends(get_verified_user)) -> User:
        """
        Fonction interne qui vérifie le rôle de l'utilisateur.
        
        Args:
            user: Utilisateur vérifié et authentifié
            
        Returns:
            User: Si le rôle est autorisé
            
        Raises:
            HTTPException: 403 si le rôle n'est pas dans la liste autorisée
        """
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissions insuffisantes. Rôles requis: {', '.join(r.value for r in roles)}"
            )
        return user
    return checker


# =============================================================================
# Dépendances prêtes à l'emploi pour une utilisation courante
# =============================================================================

# Accès standard : utilisateur vérifié (user, premium ou admin)
require_user = require_role(UserRole.user, UserRole.premium, UserRole.admin)
"""
Dépendance pour les endpoints standards.
Autorise : utilisateurs vérifiés, premium et administrateurs.
Exclut : anonymes, waitlist, et utilisateurs non vérifiés.
"""

# Accès premium : fonctionnalités payantes
require_premium = require_role(UserRole.premium, UserRole.admin)
"""
Dépendance pour les fonctionnalités premium.
Autorise : abonnés premium et administrateurs.
Exclut : utilisateurs standards (même vérifiés).
"""

# Accès administrateur : gestion complète
require_admin = require_role(UserRole.admin)
"""
Dépendance pour les endpoints d'administration.
Autorise : uniquement les administrateurs.
"""