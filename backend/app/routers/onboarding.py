"""
Router pour le canal d'onboarding.

Expose trois endpoints :
- GET  /onboarding/flow     Retourne la config du flow actif
- POST /onboarding/evaluate Évalue les réponses et retourne le résultat
- POST /onboarding/register Inscrit l'utilisateur après le flow
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.auth.security import (create_access_token, create_email_token,
                                create_refresh_token, hash_password)
from app.config import get_settings
from app.database import get_db
from app.email.service import send_verification_email
from app.limiter import limiter
from app.models import ActivityLog, RefreshToken, User, UserProfile, UserRole
from app.onboarding.engine import evaluate_scoring, load_flow, render_result_screen
from app.schemas.auth import MessageResponse
from app.schemas.onboarding import (
    OnboardingRegisterRequest,
    OnboardingEvaluateRequest,
    OnboardingUpdateProfileRequest
)
from app.auth.dependencies import get_verified_user

logger   = logging.getLogger(__name__)
router   = APIRouter(prefix="/onboarding", tags=["onboarding"])
settings = get_settings()


def _check_enabled():
    if not settings.auth_channel_onboarding:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le canal onboarding n'est pas activé",
        )


@router.get("/flow")
async def get_flow():
    """
    Retourne la configuration du flow actif (sans les règles de scoring).
    Le frontend utilise cette réponse pour afficher les étapes.
    """
    _check_enabled()
    flow = load_flow(settings.auth_onboarding_flow)
    # Ne pas exposer les règles de scoring au frontend
    return {
        "id":          flow["id"],
        "title":       flow["title"],
        "description": flow["description"],
        "steps":       flow["steps"],
    }


@router.post("/evaluate")
async def evaluate_flow(payload: OnboardingEvaluateRequest):
    """
    Évalue les réponses et retourne le résultat personnalisé.
    Appelé avant l'inscription pour montrer le profil calculé.
    """
    _check_enabled()
    answers = payload.answers
    flow    = load_flow(settings.auth_onboarding_flow)
    result  = evaluate_scoring(flow, answers)
    screen  = render_result_screen(flow, result)

    return {
        "result": result,
        "screen": screen,
    }


@router.post("/register", response_model=MessageResponse,
             status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register_onboarding(
    request:  Request,
    payload:  OnboardingRegisterRequest,
    db:       Session = Depends(get_db),
):
    """
    Inscription via le canal onboarding.
    Stocke les réponses, calcule le profil, assigne le rôle.
    """
    _check_enabled()

    email    = payload.email.lower()
    password = payload.password
    answers  = payload.answers
    fullname = payload.full_name

    # Vérification de l'unicité de l'email
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400,
                            detail="Cet email est déjà utilisé")

    # Calcul du profil et du rôle
    flow           = load_flow(settings.auth_onboarding_flow)
    scoring_result = evaluate_scoring(flow, answers)
    assigned_role  = scoring_result.get("role", "user")

    # Valider que le rôle existe
    try:
        role = UserRole(assigned_role)
    except ValueError:
        role = UserRole.user

    # Créer l'utilisateur
    user = User(
        email           = email,
        hashed_password = hash_password(password),
        full_name       = fullname,
        role            = role,
        is_verified     = False,
    )
    db.add(user)
    db.flush()

    # Stocker le profil
    actions = flow.get("actions", [])
    if "store_profile" in actions:
        profile = UserProfile(
            user_id = user.id,
            flow_id = flow["id"],
            answers = json.dumps(answers),
            profile = scoring_result.get("profile"),
            score   = scoring_result.get("score"),
        )
        db.add(profile)

    db.commit()
    db.refresh(user)

    # Envoyer l'email de vérification
    token = create_email_token(user.email, "verify")
    await send_verification_email(
        user.email, user.full_name or "Utilisateur", token
    )

    # Log
    db.add(ActivityLog(
        user_id    = user.id,
        action     = "auth.register_onboarding",
        ip_address = request.client.host if request.client else None,
        details    = json.dumps(scoring_result),
    ))
    db.commit()

    logger.info(f"auth.register_onboarding user_id={user.id} "
                f"profile={scoring_result.get('profile')} role={role}")

    return {"message": "Compte créé. Vérifiez votre email pour l'activer."}

@router.post("/update-profile", response_model=MessageResponse)
async def update_profile(
    payload: OnboardingUpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_verified_user),
):
    """Met à jour le profil onboarding d'un user connecté."""
    answers = payload.answers
    flow    = load_flow(settings.auth_onboarding_flow)
    result  = evaluate_scoring(flow, answers)

    # Mettre à jour ou créer le profil
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if profile:
        profile.answers = json.dumps(answers)
        profile.profile = result.get("profile")
        profile.score   = result.get("score")
        profile.flow_id = flow["id"]
    else:
        db.add(UserProfile(
            user_id = current_user.id,
            flow_id = flow["id"],
            answers = json.dumps(answers),
            profile = result.get("profile"),
            score   = result.get("score"),
        ))

    # Upgrader le rôle si le scoring donne premium
    new_role = result.get("role", "user")
    if new_role == "premium" and current_user.role == UserRole.user:
        current_user.role = UserRole.premium

    db.commit()
    logger.info(f"onboarding.profile_updated user_id={current_user.id} "
                f"profile={result.get('profile')}")

    return {"message": "Profil mis à jour avec succès"}

@router.get("/my-profile")
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_verified_user),
):
    """Retourne le profil onboarding de l'utilisateur connecté."""
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profil non trouvé")

    return {
        "flow_id":    profile.flow_id,
        "profile":    profile.profile,
        "score":      profile.score,
        "answers":    json.loads(profile.answers) if profile.answers else {},
        "updated_at": profile.updated_at,
    }