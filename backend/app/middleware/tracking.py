"""
Endpoint de tracking des pages frontend.

Le middleware TrackingMiddleware ne capturait que les appels API
car le frontend est une SPA (Single Page Application) — le serveur
ne reçoit jamais les routes /learn, /profile, etc.

Ce endpoint est appelé par le hook usePageTracking() à chaque
changement de route React.
"""

import hashlib
import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.database import get_db
from app.models import User, Visit

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tracking"])

# Pages admin exclues du tracking (données non pertinentes)
EXCLUDED_PREFIXES = (
    "/admin",
    "/api",
    "/uploads",
)


@router.post("/track")
async def track_page(
    request:      Request,
    payload:      dict,
    db:           Session     = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """
    Reçoit un ping du frontend à chaque navigation.
    Enregistre la visite avec géolocalisation GeoIP.
    """
    path = payload.get("path", "/")

    # Ignorer les pages admin et les paths parasites
    if any(path.startswith(p) for p in EXCLUDED_PREFIXES):
        return {"status": "skipped"}

    # IP réelle derrière Traefik
    ip = request.headers.get("X-Forwarded-For", "")
    if ip:
        ip = ip.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "0.0.0.0"

    # Hash SHA-256 pour anonymisation RGPD (16 caractères suffisent)
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]

    # Géolocalisation
    geo: dict = {}
    try:
        from app.geoip.service import lookup
        geo = lookup(ip)
    except Exception as e:
        logger.debug(f"track.geoip_failed ip={ip}: {e}")

    # Rôle de l'utilisateur
    user_role = "anonymous"
    user_id   = None
    if current_user:
        user_id   = current_user.id
        user_role = current_user.role.value \
                    if hasattr(current_user.role, "value") \
                    else str(current_user.role)

    visit = Visit(
        ip_hash      = ip_hash,
        country_code = geo.get("country_code"),
        country_name = geo.get("country_name"),
        city         = geo.get("city"),
        latitude     = geo.get("latitude"),
        longitude    = geo.get("longitude"),
        path         = path,
        user_id      = user_id,
        user_role    = user_role,
    )
    db.add(visit)

    try:
        db.commit()
        logger.debug(
            f"track.page path={path} "
            f"country={geo.get('country_code', '?')} "
            f"role={user_role}"
        )
    except Exception as e:
        db.rollback()
        logger.warning(f"track.commit_failed: {e}")

    return {"status": "ok"}
