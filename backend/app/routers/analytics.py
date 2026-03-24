"""
Endpoints analytics pour le dashboard admin.

Trois endpoints :
- /admin/analytics/world        Données par pays + coordonnées villes
- /admin/analytics/timeline     Courbe temporelle (visites/jour)
- /admin/analytics/top-countries Top N pays
"""

import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import User, Visit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/analytics", tags=["analytics"])

# Rôles valides pour le filtre
VALID_ROLES = {"anonymous", "user", "premium", "admin"}


def _base_query(db: Session, role_filter: str | None,
                days: int):
    """Construit la query de base avec filtres communs."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = db.query(Visit).filter(Visit.created_at >= since)

    if role_filter == "anonymous":
        q = q.filter(Visit.user_id == None)
    elif role_filter in VALID_ROLES:
        q = q.filter(Visit.user_role == role_filter)

    return q


@router.get("/world")
async def get_world_data(
    role:   str | None = Query(None),
    days:   int        = Query(30, ge=1, le=365),
    db:     Session    = Depends(get_db),
    _:      User       = Depends(require_admin),
):
    """
    Retourne deux datasets pour la carte :
    - countries : visites agrégées par pays (choroplèthe)
    - cities    : visites agrégées par ville avec coordonnées (points)
    """
    base = _base_query(db, role, days)

    # Agrégation par pays
    countries_raw = (
        base.with_entities(
            Visit.country_code,
            Visit.country_name,
            func.count(Visit.id).label("visits"),
        )
        .filter(Visit.country_code != None)
        .group_by(Visit.country_code, Visit.country_name)
        .order_by(desc("visits"))
        .all()
    )

    # Agrégation par ville (avec coordonnées)
    cities_raw = (
        base.with_entities(
            Visit.city,
            Visit.country_code,
            Visit.latitude,
            Visit.longitude,
            func.count(Visit.id).label("visits"),
        )
        .filter(
            Visit.latitude != None,
            Visit.longitude != None,
            Visit.city != None,
        )
        .group_by(
            Visit.city, Visit.country_code,
            Visit.latitude, Visit.longitude,
        )
        .order_by(desc("visits"))
        .limit(500)   # Limiter pour les perfs frontend
        .all()
    )

    return {
        "countries": [
            {
                "country_code": r.country_code,
                "country_name": r.country_name,
                "visits":       r.visits,
            }
            for r in countries_raw
        ],
        "cities": [
            {
                "city":         r.city,
                "country_code": r.country_code,
                "latitude":     float(r.latitude),
                "longitude":    float(r.longitude),
                "visits":       r.visits,
            }
            for r in cities_raw
        ],
        "total": base.count(),
    }


@router.get("/timeline")
async def get_timeline(
    role:  str | None = Query(None),
    days:  int        = Query(30, ge=7, le=365),
    db:    Session    = Depends(get_db),
    _:     User       = Depends(require_admin),
):
    """Retourne les visites agrégées par jour."""
    base = _base_query(db, role, days)

    daily = (
        base.with_entities(
            func.date(Visit.created_at).label("date"),
            func.count(Visit.id).label("visits"),
        )
        .group_by(func.date(Visit.created_at))
        .order_by("date")
        .all()
    )

    return {
        "data": [
            {"date": str(r.date), "visits": r.visits}
            for r in daily
        ]
    }


@router.get("/top-countries")
async def get_top_countries(
    role:  str | None = Query(None),
    days:  int        = Query(30, ge=1, le=365),
    limit: int        = Query(10, ge=1, le=50),
    db:    Session    = Depends(get_db),
    _:     User       = Depends(require_admin),
):
    """Retourne le top N des pays par nombre de visites."""
    base = _base_query(db, role, days)

    results = (
        base.with_entities(
            Visit.country_code,
            Visit.country_name,
            func.count(Visit.id).label("visits"),
        )
        .filter(Visit.country_code != None)
        .group_by(Visit.country_code, Visit.country_name)
        .order_by(desc("visits"))
        .limit(limit)
        .all()
    )

    total = base.count()

    return {
        "data": [
            {
                "country_code": r.country_code,
                "country_name": r.country_name or r.country_code,
                "visits":       r.visits,
                "pct":          round(r.visits / total * 100, 1)
                                if total else 0,
            }
            for r in results
        ],
        "total": total,
    }