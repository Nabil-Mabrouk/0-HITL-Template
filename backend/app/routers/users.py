"""
Router FastAPI pour la gestion du profil utilisateur.

Ce module gère les opérations liées au compte utilisateur :
- Consultation et modification du profil
- Changement de mot de passe avec révocation des sessions
- Suppression de compte (soft delete)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_verified_user
from app.auth.security import hash_password, verify_password
from app.database import get_db
from app.limiter import limiter
from app.models import RefreshToken, User
from app.schemas.users import MessageResponse, UpdateProfileRequest, UserProfile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Obtenir mon profil",
    description="Retourne les informations du profil de l'utilisateur connecté.",
)
async def get_profile(
    current_user: User = Depends(get_verified_user),
) -> UserProfile:
    """
    Récupère le profil de l'utilisateur authentifié.
    
    Args:
        current_user: Utilisateur injecté via la dépendance d'authentification
        
    Returns:
        UserProfile: Données du profil utilisateur
    """
    return current_user


@router.put(
    "/me",
    response_model=UserProfile,
    summary="Mettre à jour mon profil",
    description="Modifie les informations du profil (nom, etc.).",
)
@limiter.limit("10/minute")
async def update_profile(
    request: Request,
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_verified_user),
) -> UserProfile:
    """
    Met à jour les informations du profil utilisateur.
    
    Args:
        request: Requête HTTP (requis par le rate limiter)
        payload: Données de mise à jour
        db: Session de base de données
        current_user: Utilisateur authentifié
        
    Returns:
        UserProfile: Profil mis à jour
        
    Note:
        Seuls les champs fournis sont mis à jour (patch sémantique).
    """
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
        logger.info(f"users.profile.updated user_id={current_user.id} field=full_name")

    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.put(
    "/me/password",
    response_model=MessageResponse,
    summary="Changer le mot de passe",
    description="""
    Modifie le mot de passe après vérification de l'ancien.
    
    Sécurité : révoque toutes les sessions existantes, forçant une
    reconnexion avec le nouveau mot de passe.
    """,
)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_verified_user),
) -> MessageResponse:
    """
    Change le mot de passe de l'utilisateur.
    
    Pour des raisons de sécurité, cette opération :
    1. Vérifie le mot de passe actuel
    2. Valide la complexité du nouveau mot de passe
    3. Révoque toutes les sessions existantes
    4. Force une reconnexion
    
    Args:
        request: Requête HTTP
        payload: Contient current_password et new_password
        db: Session de base de données
        current_user: Utilisateur authentifié
        
    Raises:
        HTTPException: 400 si mot de passe actuel incorrect ou nouveau trop court
    """
    # Vérification du mot de passe actuel
    current_password = payload.get("current_password", "")
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect",
        )

    # Validation du nouveau mot de passe
    new_password = payload.get("new_password", "")
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nouveau mot de passe doit contenir au moins 8 caractères",
        )

    # Mise à jour du hash
    current_user.hashed_password = hash_password(new_password)
    
    # Sécurité : révocation de toutes les sessions
    # L'utilisateur devra se reconnecter avec son nouveau mot de passe
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id
    ).update({"revoked": True})
    
    db.commit()
    
    logger.info(f"users.password.changed user_id={current_user.id}")

    return {
        "message": "Mot de passe modifié avec succès. Veuillez vous reconnecter avec votre nouveau mot de passe."
    }


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Supprimer mon compte",
    description="""
    Suppression du compte utilisateur (soft delete).
    
    - Désactive le compte (is_active = False)
    - Anonymise l'email pour libérer l'adresse
    - Révoque toutes les sessions
    - Conserve les logs pour audit légal
    """,
)
@limiter.limit("3/minute")
async def delete_account(
    request: Request,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_verified_user),
) -> MessageResponse:
    """
    Supprime le compte utilisateur (soft delete).
    
    Cette opération ne supprime pas physiquement les données pour :
    - Conserver les logs d'activité (obligations légales)
    - Permettre une éventuelle restauration
    - Libérer l'adresse email pour une réinscription future
    
    Args:
        request: Requête HTTP
        payload: Contient le mot de passe pour confirmation
        db: Session de base de données
        current_user: Utilisateur à supprimer
        
    Raises:
        HTTPException: 400 si mot de passe de confirmation incorrect
    """
    # Confirmation par mot de passe pour éviter les suppressions accidentelles
    password = payload.get("password", "")
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe incorrect. La suppression a été annulée.",
        )

    # Soft delete : désactivation plutôt que suppression physique
    current_user.is_active = False
    
    # Anonymisation de l'email pour :
    # 1. Libérer l'adresse pour une future inscription
    # 2. Respecter le RGPD (droit à l'oubli partiel)
    # 3. Maintenir l'intégrité référentielle des logs
    original_email = current_user.email
    current_user.email = f"deleted_{current_user.id}@deleted.invalid"
    
    # Révocation immédiate de toutes les sessions
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id
    ).update({"revoked": True})
    
    db.commit()

    logger.info(
        f"users.account_deleted user_id={current_user.id} "
        f"original_email_hash={hash(original_email) % 10000}"  # Hash partiel pour privacy
    )

    return {
        "message": "Votre compte a été supprimé avec succès. Vous pouvez récréer un compte avec la même adresse email si vous le souhaitez."
    }