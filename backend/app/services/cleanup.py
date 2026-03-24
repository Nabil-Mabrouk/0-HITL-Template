"""
Service de nettoyage de la base de données.

Supprime les données expirées selon les paramètres configurés
dans la table db_settings.
"""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import RefreshToken, Visit, ActivityLog, DbSettings

logger = logging.getLogger(__name__)


def get_or_create_settings(db: Session) -> DbSettings:
    """Retourne les paramètres DB, en les créant si absents."""
    settings = db.query(DbSettings).filter(DbSettings.id == 1).first()
    if not settings:
        settings = DbSettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def run_cleanup(db: Session | None = None) -> dict:
    """
    Exécute le nettoyage complet selon les paramètres DB.
    Peut être appelé manuellement ou par le scheduler.
    """
    close_db = False
    if db is None:
        db       = SessionLocal()
        close_db = True

    try:
        cfg = get_or_create_settings(db)
        now = datetime.now(timezone.utc)

        results = {}

        # ── Refresh tokens expirés ou révoqués anciens ────────────────
        token_cutoff = now - timedelta(days=cfg.tokens_retention_days)
        deleted_tokens = (
            db.query(RefreshToken)
            .filter(
                (RefreshToken.expires_at < now) |
                (
                    (RefreshToken.revoked == True) &
                    (RefreshToken.created_at < token_cutoff)
                )
            )
            .delete(synchronize_session=False)
        )
        results["tokens_deleted"] = deleted_tokens

        # ── Visits anciennes ──────────────────────────────────────────
        visit_cutoff = now - timedelta(days=cfg.visits_retention_days)
        deleted_visits = (
            db.query(Visit)
            .filter(Visit.created_at < visit_cutoff)
            .delete(synchronize_session=False)
        )
        results["visits_deleted"] = deleted_visits

        # ── Logs d'activité anciens ───────────────────────────────────
        log_cutoff = now - timedelta(days=cfg.logs_retention_days)
        deleted_logs = (
            db.query(ActivityLog)
            .filter(ActivityLog.created_at < log_cutoff)
            .delete(synchronize_session=False)
        )
        results["logs_deleted"] = deleted_logs

        # Mettre à jour la date de dernier nettoyage
        cfg.last_cleanup_at = now
        db.commit()

        total = sum(results.values())
        logger.info(
            f"cleanup.completed tokens={deleted_tokens} "
            f"visits={deleted_visits} logs={deleted_logs} "
            f"total={total}"
        )

        return {**results, "total_deleted": total,
                "executed_at": now.isoformat()}

    except Exception as e:
        db.rollback()
        logger.error(f"cleanup.error: {e}")
        raise
    finally:
        if close_db:
            db.close()