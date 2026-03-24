"""
Router FastAPI pour l'authentification et la gestion des sessions.

Ce module gère :
- L'inscription avec vérification d'invitation (waitlist)
- La connexion avec JWT (access + refresh tokens)
- La rotation sécurisée des refresh tokens
- La vérification d'email
- La réinitialisation de mot de passe
- La déconnexion (révocation des tokens)
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import (
    create_access_token,
    create_email_token,
    create_refresh_token,
    decode_email_token,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.database import get_db
from app.email.service import send_reset_password_email, send_verification_email
from app.limiter import limiter
from app.models import ActivityLog, RefreshToken, User, UserRole
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterDirectRequest,
    TokenResponse,
)

# Configuration du logger et du router
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def log_activity(
    db: Session,
    user_id: int | None,
    action: str,
    request: Request,
    details: str | None = None,
) -> None:
    """
    Enregistre une action dans le journal d'activité.
    
    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur (None pour actions anonymes)
        action: Type d'action (ex: "auth.login.success")
        request: Requête HTTP pour extraire IP et User-Agent
        details: Informations additionnelles (optionnel)
    """
    log_entry = ActivityLog(
        user_id=user_id,
        action=action,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=details,
    )
    db.add(log_entry)
    db.commit()


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscription avec invitation",
    description="""
    Crée un compte utilisateur à partir d'un token d'invitation de la waitlist.
    
    - Vérifie la validité du token d'invitation
    - Supprime l'entrée de la waitlist après inscription
    - Envoie un email de vérification d'adresse
    """,
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Inscription d'un nouvel utilisateur via invitation.
    
    Le token d'invitation doit provenir de la waitlist. Une fois utilisé,
    il est invalidé et l'entrée waitlist est supprimée.
    """
    # Import local pour éviter les imports circulaires
    from app.models import WaitlistEntry

    # Vérification du token d'invitation
    waitlist_entry = (
        db.query(WaitlistEntry)
        .filter(WaitlistEntry.invitation_token == payload.invitation_token)
        .first()
    )

    if not waitlist_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token d'invitation invalide ou déjà utilisé",
        )

    # Sécurité : vérifier que l'email correspond à l'invitation
    if waitlist_entry.email != payload.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email ne correspond pas à l'invitation",
        )

    # Vérification de l'unicité de l'email
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé",
        )

    # Création de l'utilisateur
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.user,
        is_verified=False,  # Doit vérifier son email avant première connexion
    )
    db.add(user)
    db.flush()  # Obtient l'ID sans commiter la transaction

    # Nettoyage de la waitlist
    db.delete(waitlist_entry)
    db.commit()
    db.refresh(user)

    # Envoi de l'email de vérification
    verification_token = create_email_token(user.email, "verify")
    await send_verification_email(
        user.email, user.full_name or "Utilisateur", verification_token
    )

    # Logging
    log_activity(db, user.id, "auth.register", request)
    logger.info(f"auth.register.success user_id={user.id} email={user.email}")

    return {
        "message": "Compte créé avec succès. Vérifiez votre email pour l'activer."
    }


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Connexion",
    description="Authentifie un utilisateur et retourne les tokens JWT.",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authentification d'un utilisateur.
    
    Vérifie les credentials et retourne un access token (JWT).
    Le refresh token est envoyé via un cookie sécurisé HttpOnly.
    """
    # Recherche de l'utilisateur (case insensitive sur l'email)
    user = (
        db.query(User)
        .filter(User.email == payload.email.lower())
        .first()
    )

    # Vérification des credentials (même message d'erreur pour éviter l'énumération)
    if not user or not verify_password(payload.password, user.hashed_password):
        log_activity(db, user.id if user else None, "auth.login.failed", request, payload.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    # Vérifications de l'état du compte
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte suspendu. Contactez le support.",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email non vérifié. Consultez votre boîte de réception.",
        )

    # Génération des tokens
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token_value = create_refresh_token()

    # Stockage du refresh token
    max_age = settings.refresh_token_expire_days * 24 * 3600
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=max_age)
    
    db_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()

    # Configuration du cookie HttpOnly
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_value,
        httponly=True,
        max_age=max_age,
        expires=max_age,
        samesite="lax",
        secure=True,  # Toujours utiliser secure en prod
    )

    log_activity(db, user.id, "auth.login.success", request)
    logger.info(f"auth.login.success user_id={user.id}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rafraîchir les tokens",
    description="""
    Échange un refresh token valide contre un nouveau access token.
    
    Implémente la rotation des refresh tokens :
    - L'ancien refresh token est révoqué
    - Un nouveau refresh token est généré et retourné via cookie
    """,
)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Rotation sécurisée des tokens via cookies.
    """
    # Récupération du token depuis le cookie
    refresh_token_value = request.cookies.get("refresh_token")

    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée ou invalide",
        )

    # Recherche du token non révoqué
    db_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token == refresh_token_value,
            RefreshToken.revoked == False,
        )
        .first()
    )

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide ou révoquée",
        )

    # Vérification de l'expiration
    if db_token.expires_at < datetime.now(timezone.utc):
        db_token.revoked = True
        db.commit()
        response.delete_cookie("refresh_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée. Veuillez vous reconnecter.",
        )

    user = db_token.user
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte suspendu",
        )

    # Rotation du token : révocation de l'ancien
    db_token.revoked = True

    # Création du nouveau refresh token
    new_refresh_token = create_refresh_token()
    max_age = settings.refresh_token_expire_days * 24 * 3600
    new_expires = datetime.now(timezone.utc) + timedelta(seconds=max_age)
    
    db.add(
        RefreshToken(
            user_id=user.id,
            token=new_refresh_token,
            expires_at=new_expires,
        )
    )
    db.commit()

    # Mise à jour du cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        max_age=max_age,
        expires=max_age,
        samesite="lax",
        secure=True,
    )

    # Génération du nouvel access token
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Déconnexion",
    description="Révoque le refresh token et termine la session.",
)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """
    Déconnexion sécurisée via cookies.
    """
    refresh_token_value = request.cookies.get("refresh_token")

    if refresh_token_value:
        db_token = (
            db.query(RefreshToken)
            .filter(
                RefreshToken.token == refresh_token_value,
                RefreshToken.user_id == current_user.id,
            )
            .first()
        )

        if db_token:
            db_token.revoked = True
            db.commit()

    # Suppression du cookie
    response.delete_cookie("refresh_token")

    log_activity(db, current_user.id, "auth.logout", request)
    logger.info(f"auth.logout user_id={current_user.id}")

    return {"message": "Déconnexion réussie"}


@router.get(
    "/verify-email",
    response_model=MessageResponse,
    summary="Vérifier l'email",
    description="Valide le token de vérification et active le compte.",
)
async def verify_email(
    token: str,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Vérification d'adresse email.
    
    Décode le token signé et active le compte utilisateur correspondant.
    """
    email = decode_email_token(token, "verify")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalide ou expiré",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )

    user.is_verified = True
    db.commit()

    logger.info(f"auth.email_verified user_id={user.id} email={email}")
    return {"message": "Email vérifié avec succès. Vous pouvez maintenant vous connecter."}


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Mot de passe oublié",
    description="""
    Demande de réinitialisation de mot de passe.
    
    Retourne toujours le même message pour éviter l'énumération
    des adresses email présentes dans la base.
    """,
)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    payload: dict,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Initie le processus de réinitialisation de mot de passe.
    
    Pour des raisons de sécurité (privacy), retourne toujours le même
    message que l'email existe ou non.
    """
    email = payload.get("email", "").lower().strip()
    
    # Validation basique du format email
    if not email or "@" not in email:
        # Même réponse pour ne pas révéler si le format est invalide
        return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}

    user = db.query(User).filter(User.email == email).first()

    # Envoi uniquement si l'utilisateur existe et est actif
    if user and user.is_active:
        reset_token = create_email_token(email, "reset")
        await send_reset_password_email(email, reset_token)
        logger.info(f"auth.password_reset.requested email={email}")

    # Réponse identique dans tous les cas
    return {
        "message": "Si cet email existe dans notre base, un lien de réinitialisation a été envoyé."
    }


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Réinitialiser le mot de passe",
    description="Valide le token et met à jour le mot de passe.",
)
@limiter.limit("5/minute")
async def reset_password(
    request: Request,
    payload: dict,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Réinitialisation effective du mot de passe.
    
    Valide le token, met à jour le mot de passe, et révoque toutes les
    sessions existantes (sécurité).
    """
    token = payload.get("token", "")
    password = payload.get("password", "")

    # Validation de la complexité du mot de passe
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe doit contenir au moins 8 caractères",
        )

    # Validation du token
    email = decode_email_token(token, "reset")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalide ou expiré",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable",
        )

    # Mise à jour du mot de passe
    user.hashed_password = hash_password(password)

    # Sécurité : révocation de toutes les sessions existantes
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).update(
        {"revoked": True}
    )
    db.commit()

    log_activity(db, user.id, "auth.password_reset", request)
    logger.info(f"auth.password_reset.completed user_id={user.id}")

    return {"message": "Mot de passe réinitialisé avec succès. Veuillez vous reconnecter."}

@router.post(
    "/register-direct",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscription directe (canal open)",
)
@limiter.limit("5/minute")
async def register_direct(
    request: Request,
    payload: RegisterDirectRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    """
    Inscription sans invitation — canal direct.
    Désactivé si AUTH_CHANNEL_DIRECT=false.
    """
    if not settings.auth_channel_direct:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="L'inscription directe n'est pas activée",
        )

    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé",
        )

    user = User(
        email           = payload.email.lower(),
        hashed_password = hash_password(payload.password),
        full_name       = payload.full_name,
        role            = UserRole.user,
        is_verified     = False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_email_token(user.email, "verify")
    await send_verification_email(
        user.email, user.full_name or "Utilisateur", token
    )

    log_activity(db, user.id, "auth.register_direct", request)
    logger.info(f"auth.register_direct.success user_id={user.id}")

    return {"message": "Compte créé. Vérifiez votre email pour l'activer."}