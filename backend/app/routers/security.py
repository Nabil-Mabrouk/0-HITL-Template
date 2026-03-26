"""
Endpoints d'administration pour les événements de sécurité.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin
from ..database import get_db
from ..models import SecurityEvent, User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/security", tags=["security"])


@router.get("/events")
async def list_events(
    page:       int           = Query(1, ge=1),
    per_page:   int           = Query(50, ge=1, le=200),
    severity:   Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    ip:         Optional[str] = Query(None),
    days:       int           = Query(7, ge=1, le=90),
    db:         Session       = Depends(get_db),
    _:          User          = Depends(require_admin),
):
    """Liste paginée des événements de sécurité."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = db.query(SecurityEvent).filter(SecurityEvent.created_at >= since)

    if severity:
        query = query.filter(SecurityEvent.severity == severity)
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if ip:
        query = query.filter(SecurityEvent.ip_address == ip)

    total  = query.count()
    events = (
        query.order_by(desc(SecurityEvent.created_at))
             .offset((page - 1) * per_page)
             .limit(per_page)
             .all()
    )

    return {
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "events": [
            {
                "id":         e.id,
                "event_type": e.event_type,
                "severity":   e.severity,
                "ip_address": e.ip_address,
                "path":       e.path,
                "method":     e.method,
                "user_agent": e.user_agent,
                "details":    e.details,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }


@router.get("/summary")
async def security_summary(
    days: int     = Query(7, ge=1, le=90),
    db:   Session = Depends(get_db),
    _:    User    = Depends(require_admin),
):
    """Résumé des événements : totaux par type, par sévérité, top IPs."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    base  = db.query(SecurityEvent).filter(SecurityEvent.created_at >= since)

    # Totaux par sévérité
    by_severity = dict(
        db.query(SecurityEvent.severity, func.count(SecurityEvent.id))
          .filter(SecurityEvent.created_at >= since)
          .group_by(SecurityEvent.severity)
          .all()
    )

    # Totaux par type
    by_type = dict(
        db.query(SecurityEvent.event_type, func.count(SecurityEvent.id))
          .filter(SecurityEvent.created_at >= since)
          .group_by(SecurityEvent.event_type)
          .all()
    )

    # Top 10 IPs agressives
    top_ips = (
        db.query(SecurityEvent.ip_address, func.count(SecurityEvent.id).label("hits"))
          .filter(SecurityEvent.created_at >= since)
          .group_by(SecurityEvent.ip_address)
          .order_by(desc("hits"))
          .limit(10)
          .all()
    )

    # Dernières 24h
    last_24h = base.filter(
        SecurityEvent.created_at >= datetime.now(timezone.utc) - timedelta(hours=24)
    ).count()

    return {
        "total":       base.count(),
        "last_24h":    last_24h,
        "by_severity": by_severity,
        "by_type":     by_type,
        "top_ips":     [{"ip": ip, "hits": hits} for ip, hits in top_ips],
    }


@router.delete("/events/old")
async def purge_old_events(
    days: int     = Query(30, ge=7, le=365),
    db:   Session = Depends(get_db),
    _:    User    = Depends(require_admin),
):
    """Supprime les événements plus anciens que N jours."""
    cutoff  = datetime.now(timezone.utc) - timedelta(days=days)
    deleted = db.query(SecurityEvent)\
                .filter(SecurityEvent.created_at < cutoff)\
                .delete()
    db.commit()
    logger.info(f"security.purge deleted={deleted} older_than={days}d")
    return {"deleted": deleted}
