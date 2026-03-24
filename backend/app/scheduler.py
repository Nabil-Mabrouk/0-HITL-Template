"""
Scheduler de tâches de maintenance.
Utilise APScheduler avec le backend mémoire (simple, sans DB externe).
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron      import CronTrigger
from app.services.cleanup           import run_cleanup, get_or_create_settings
from app.database                   import SessionLocal

logger    = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def schedule_cleanup():
    """
    Planifie le nettoyage selon la fréquence configurée dans DB.
    Appelé au démarrage et après chaque modification des paramètres.
    """
    # Supprimer le job existant si présent
    if scheduler.get_job("db_cleanup"):
        scheduler.remove_job("db_cleanup")

    db  = SessionLocal()
    try:
        cfg = get_or_create_settings(db)
        freq = cfg.cleanup_frequency
    finally:
        db.close()

    if freq == "disabled":
        logger.info("scheduler.cleanup disabled")
        return

    triggers = {
        "daily":   CronTrigger(hour=3, minute=0),        # 3h du matin
        "weekly":  CronTrigger(day_of_week="mon",
                               hour=3, minute=0),         # lundi 3h
        "monthly": CronTrigger(day=1, hour=3, minute=0), # 1er du mois 3h
    }

    trigger = triggers.get(freq)
    if not trigger:
        return

    scheduler.add_job(
        func        = run_cleanup,
        trigger     = trigger,
        id          = "db_cleanup",
        name        = "Database cleanup",
        replace_existing = True,
    )
    logger.info(f"scheduler.cleanup scheduled frequency={freq}")


def start_scheduler():
    """Démarre le scheduler au démarrage de l'application."""
    schedule_cleanup()
    if not scheduler.running:
        scheduler.start()
        logger.info("scheduler.started")


def stop_scheduler():
    """Arrête proprement le scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("scheduler.stopped")