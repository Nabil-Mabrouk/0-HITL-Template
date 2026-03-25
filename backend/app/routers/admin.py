"""
Router FastAPI pour l'administration de la plateforme.

Ce module fournit les endpoints réservés aux administrateurs pour :
- Consulter les statistiques globales
- Gérer les utilisateurs (CRUD, rôles, suspension)
- Auditer les logs d'activité
- Gérer la liste d'attente (envoi d'invitations)
"""

import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.auth.security import create_email_token
from app.database import get_db
from app.email.service import send_invitation_email
from app.models import ActivityLog, User, UserRole, WaitlistEntry
from app.schemas.admin import (
    ActivityLogView,
    StatsResponse,
    UpdateRoleRequest,
    UserAdminView,
    UserListResponse,
    WaitlistListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Statistiques globales",
    description="Retourne les métriques clés de la plateforme.",
)
async def get_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> StatsResponse:
    """
    Calcule et retourne les statistiques globales de la plateforme.
    
    Métriques inclues :
    - Utilisateurs totaux, actifs, vérifiés, premium
    - État de la liste d'attente (total, en attente d'invitation)
    
    Args:
        db: Session de base de données
        _: Administrateur authentifié (via require_admin)
        
    Returns:
        StatsResponse: Dictionnaire des statistiques
    """
    return {
        "total_users": db.query(User).count(),
        "active_users": db.query(User).filter(User.is_active == True).count(),
        "verified_users": db.query(User).filter(User.is_verified == True).count(),
        "premium_users": db.query(User).filter(User.role == UserRole.premium).count(),
        "waitlist_total": db.query(WaitlistEntry).count(),
        "waitlist_pending": db.query(WaitlistEntry)
                            .filter(WaitlistEntry.invited_at.is_(None))
                            .count(),
    }


@router.get(
    "/waitlist",
    response_model=WaitlistListResponse,
    summary="Lister la waitlist",
    description="Liste paginée de la liste d'attente.",
)
async def list_waitlist(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> WaitlistListResponse:
    """Liste paginée des entrées de la waitlist."""
    query = db.query(WaitlistEntry)
    total = query.count()
    entries = (
        query.order_by(desc(WaitlistEntry.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "entries": entries,
    }


@router.put(
    "/users/{user_id}/role",
    response_model=UserAdminView,
    summary="Modifier le rôle d'un utilisateur",
    description="Change le rôle (user, premium, admin) d'un utilisateur.",
)
async def update_user_role(
    user_id: int,
    payload: UpdateRoleRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserAdminView:
    """
    Modifie le rôle d'un utilisateur.
    
    Security:
        - Un administrateur ne peut pas modifier son propre rôle
          (évite de se rétrograder et de perdre l'accès admin)
    
    Args:
        user_id: ID de l'utilisateur cible
        payload: Nouveau rôle à attribuer
        db: Session de base de données
        admin: Administrateur effectuant l'action (pour audit)
        
    Raises:
        HTTPException: 404 si utilisateur inexistant, 400 si auto-modification
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )
    
    # Protection contre la rétrogradation de soi-même
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de modifier son propre rôle",
        )

    old_role = user.role
    user.role = payload.role
    db.commit()
    db.refresh(user)

    logger.info(
        f"admin.role_change user_id={user_id} "
        f"old={old_role.value} new={payload.role.value} "
        f"by_admin={admin.id}"
    )
    return user


@router.put(
    "/users/{user_id}/suspend",
    response_model=UserAdminView,
    summary="Suspendre/Réactiver un utilisateur",
    description="Bascule l'état actif/inactif d'un compte utilisateur.",
)
async def suspend_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserAdminView:
    """
    Suspend ou réactive un compte utilisateur (toggle).
    
    Un compte suspendu (is_active=False) ne peut pas se connecter.
    C'est un soft ban qui préserve les données pour investigation.
    
    Security:
        - Auto-protection : impossible de se suspendre soi-même
    
    Args:
        user_id: ID de l'utilisateur cible
        db: Session de base de données
        admin: Administrateur effectuant l'action
        
    Returns:
        UserAdminView: État mis à jour de l'utilisateur
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )
    
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de suspendre son propre compte",
        )

    # Toggle de l'état actif
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    action = "suspend" if not user.is_active else "reactivate"
    logger.info(f"admin.{action} user_id={user_id} by_admin={admin.id}")
    
    return user


@router.delete(
    "/users/{user_id}",
    summary="Supprimer un utilisateur",
    description="Suppression définitive d'un compte utilisateur.",
)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict[str, str]:
    """
    Supprime définitivement un compte utilisateur.
    
    DANGER: Cette action est irréversible et supprime toutes les données
    associées (cascade configurée dans les modèles).
    
    Security:
        - Impossible de supprimer un autre administrateur
          (protection contre la suppression de tous les admins)
    
    Args:
        user_id: ID de l'utilisateur à supprimer
        db: Session de base de données
        admin: Administrateur effectuant la suppression
        
    Raises:
        HTTPException: 404 si inexistant, 400 si tentative de suppression d'admin
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )
    
    # Protection : impossible de supprimer un autre admin
    if user.role == UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer un administrateur. Rétrogradez-le d'abord.",
        )

    db.delete(user)
    db.commit()
    
    logger.info(f"admin.delete user_id={user_id} by_admin={admin.id}")
    
    return {"message": "Utilisateur supprimé définitivement"}


@router.get(
    "/users/{user_id}/logs",
    response_model=list[ActivityLogView],
    summary="Logs d'activité d'un utilisateur",
    description="Retourne l'historique des actions d'un utilisateur spécifique.",
)
async def get_user_logs(
    user_id: int,
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de logs"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[ActivityLogView]:
    """
    Récupère les logs d'activité d'un utilisateur pour audit.
    
    Args:
        user_id: ID de l'utilisateur à auditer
        limit: Nombre maximum de logs à retourner (défaut 50, max 200)
        db: Session de base de données
        _: Administrateur authentifié
        
    Returns:
        list[ActivityLogView]: Logs ordonnés du plus récent au plus ancien
    """
    return (
        db.query(ActivityLog)
        .filter(ActivityLog.user_id == user_id)
        .order_by(desc(ActivityLog.created_at))
        .limit(limit)
        .all()
    )


@router.post(
    "/waitlist/{waitlist_id}/invite",
    summary="Inviter depuis la waitlist",
    description="Génère un token d'invitation et envoie l'email à un inscrit.",
)
async def invite_from_waitlist(
    waitlist_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict[str, str]:
    """
    Convertit une entrée de la waitlist en invitation envoyée.
    
    Processus :
    1. Génère un token d'invitation unique
    2. Enregistre la date d'invitation
    3. Envoie l'email avec le lien d'inscription privilégié
    
    Args:
        waitlist_id: ID de l'entrée dans la table waitlist
        db: Session de base de données
        admin: Administrateur effectuant l'invitation
        
    Raises:
        HTTPException: 404 si entrée inexistante, 400 si déjà invité
    """
    entry = db.query(WaitlistEntry).filter(WaitlistEntry.id == waitlist_id).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrée introuvable dans la liste d'attente",
        )
    
    if entry.invited_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet utilisateur a déjà reçu une invitation",
        )

    # Génération du token d'invitation (opaque, stocké en base)
    invitation_token = secrets.token_urlsafe(32)
    entry.invitation_token = invitation_token
    entry.invited_at = datetime.now(timezone.utc)
    db.commit()

    # Envoi asynchrone de l'email d'invitation
    await send_invitation_email(entry.email, invitation_token)
    
    logger.info(f"admin.invite_sent waitlist_id={waitlist_id} email={entry.email} by_admin={admin.id}")
    
    return {"message": f"Invitation envoyée avec succès à {entry.email}"}

@router.post("/bootstrap-admin")
async def bootstrap_admin(payload: dict, db: Session = Depends(get_db)):
        """Crée le premier admin. Désactivé si un admin existe déjà."""
        if db.query(User).filter(User.role == UserRole.admin).first():
            raise HTTPException(status_code=403,
                                detail="Un admin existe déjà")

        from app.auth.security import hash_password
        user = User(
            email           = payload["email"],
            hashed_password = hash_password(payload["password"]),
            full_name       = payload.get("full_name", "Admin"),
            role            = UserRole.admin,
            is_active       = True,
            is_verified     = True,
        )
        db.add(user)
        db.commit()
        return {"message": f"Admin créé : {payload['email']}"}

@router.post("/waitlist/{waitlist_id}/reinvite")
async def reinvite_from_waitlist(
    waitlist_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    entry = db.query(WaitlistEntry).filter(
        WaitlistEntry.id == waitlist_id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entrée introuvable")

    from datetime import datetime, timezone
    token = secrets.token_urlsafe(32)
    entry.invitation_token = token
    entry.invited_at = datetime.now(timezone.utc)
    db.commit()

    await send_invitation_email(entry.email, token)
    logger.info(f"admin.reinvite email={entry.email} by admin={admin.id}")
    return {"message": f"Invitation renvoyée à {entry.email}"}

@router.get("/users", response_model=UserListResponse)
async def list_users(
    page:         int = Query(1, ge=1),
    per_page:     int = Query(20, ge=1, le=100),
    search:       str = Query(""),
    role:         UserRole | None = None,
    show_deleted: bool = Query(False),   # <- nouveau paramètre
    db:           Session = Depends(get_db),
    _:            User = Depends(require_admin),
):
    query = db.query(User)

    # Par défaut — masquer les comptes supprimés (email = deleted_*)
    if not show_deleted:
        query = query.filter(
            ~User.email.like("deleted_%@deleted.invalid")
        )

    if search:
        query = query.filter(
            User.email.ilike(f"%{search}%") |
            User.full_name.ilike(f"%{search}%")
        )
    if role:
        query = query.filter(User.role == role)

    total = query.count()
    users = query.order_by(desc(User.created_at))\
                 .offset((page - 1) * per_page)\
                 .limit(per_page).all()

    return {"total": total, "page": page,
            "per_page": per_page, "users": users}