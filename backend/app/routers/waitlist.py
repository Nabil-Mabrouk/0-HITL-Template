"""
Router FastAPI pour la gestion de la liste d'attente (waitlist).

Ce module définit les endpoints pour :
- L'inscription à la liste d'attente (avec rate limiting)
- La consultation du nombre d'inscrits (statistiques)
"""

import logging
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_db
from ..models import WaitlistEntry
from app.schemas.waitlist import WaitlistCreate, WaitlistResponse
from app.limiter import limiter

# Logger structuré pour ce module
logger = logging.getLogger(__name__)

# Création du router avec préfixe et tags pour la documentation OpenAPI
router = APIRouter(
    prefix="",  # Préfixe défini au niveau de l'application (main.py)
    tags=["waitlist"],
    responses={
        429: {"description": "Trop de requêtes - rate limit dépassé"},
        500: {"description": "Erreur serveur interne"},
    },
)


@router.post(
    "/waitlist",
    response_model=WaitlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscrire un email à la liste d'attente",
    description="""
    Inscrit une nouvelle adresse email à la liste d'attente.
    
    - Limite : 5 inscriptions par minute par adresse IP
    - Les emails temporaires sont rejetés (validation Pydantic)
    - Si l'email existe déjà, retourne un succès silencieux (sécurité)
    """,
)
@limiter.limit("5/minute")  # Protection contre les abus par IP
async def join_waitlist(
    request: Request,
    payload: WaitlistCreate,
    db: Session = Depends(get_db),
) -> WaitlistResponse:
    """
    Inscrit un nouvel utilisateur à la liste d'attente.
    
    Args:
        request: Objet Request FastAPI (requis par le rate limiter)
        payload: Données validées contenant l'email
        db: Session de base de données injectée
        
    Returns:
        WaitlistResponse: Message de confirmation
        
    Security:
        - Rate limiting: 5 requêtes/minute par IP
        - Privacy: Ne révèle pas si l'email existe déjà
    """
    # Log de la tentative (sans l'email complet pour la privacy)
    domain = payload.email.split("@")[1]
    logger.info(
        "waitlist.signup.attempt",
        extra={"email_domain": domain, "client_ip": request.client.host}
    )
    
    # Création de l'entrée
    entry = WaitlistEntry(email=payload.email)
    
    try:
        db.add(entry)
        db.commit()
        logger.info("waitlist.signup.success", extra={"email_domain": domain})
        
    except IntegrityError:
        # Email déjà présent dans la base
        db.rollback()
        logger.info(
            "waitlist.signup.duplicate",  # 'failure' renommé en 'duplicate' pour clarté
            extra={"email_domain": domain}
        )
        # Retourne un succès silencieux pour ne pas exposer les emails existants
        # (protection contre l'énumération d'emails)
        return WaitlistResponse(message="Vous êtes sur la liste !")

    return WaitlistResponse(message="Vous êtes sur la liste !")


@router.get(
    "/waitlist/count",
    summary="Obtenir le nombre d'inscrits",
    description="Retourne le nombre total d'inscriptions à la liste d'attente.",
    response_description="Nombre total d'inscrits",
)
def waitlist_count(
    db: Session = Depends(get_db)
) -> dict[str, int]:
    """
    Compte le nombre total d'inscriptions dans la liste d'attente.
    
    Args:
        db: Session de base de données injectée
        
    Returns:
        dict: Dictionnaire contenant le nombre total sous la clé 'count'
        
    Example:
        >>> {"count": 42}
    """
    count = db.query(WaitlistEntry).count()
    logger.debug("waitlist.count.queried", extra={"count": count})
    
    return {"count": count}