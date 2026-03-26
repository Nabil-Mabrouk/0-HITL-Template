"""
Module principal de l'application FastAPI pour l'API 0-HITL.

Ce module configure l'application FastAPI avec :
- La limitation de débit (rate limiting) via SlowAPI
- La gestion des CORS
- La journalisation structurée en JSON
- La vérification de santé de l'application (health check)
- Le bootstrap automatique de l'admin
- Le scheduler de maintenance
- Le framework multi-agents
"""

from contextlib import asynccontextmanager
import json
import logging
import os
import sys
from datetime import datetime, timezone

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from .database import get_db, SessionLocal
from .limiter import limiter
from .config import get_settings
from .routers import auth, users, admin, waitlist, onboarding, seo
from .routers import content, admin_content, media, admin_db
from .routers import tracking
from .routers import analytics
from .routers import agent_services
from .routers import shop, shop_webhook, subscription, admin_shop
from .routers import security as security_router
from .middleware.security import SecurityMiddleware

#from .middleware.tracking import TrackingMiddleware
from .scheduler import start_scheduler, stop_scheduler
# from app.agents import discover_and_register
# from app.agents.router import router as agents_router

# ── Dossier uploads ───────────────────────────────────────────────────────────
os.makedirs("uploads", exist_ok=True)

# ── Logging JSON ──────────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)
        return json.dumps(log, ensure_ascii=False)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

# ── Bootstrap Admin ───────────────────────────────────────────────────────────

async def create_default_admin() -> None:
    """
    Crée l'admin par défaut au premier démarrage si ADMIN_EMAIL
    et ADMIN_PASSWORD sont définis dans les variables d'environnement.

    Si un admin existe déjà, ne fait rien.
    Envoie un email de bienvenue avec un lien de reset password.
    """
    if not settings.admin_email or not settings.admin_password:
        logger.info("bootstrap.admin_skipped "
                    "(ADMIN_EMAIL ou ADMIN_PASSWORD non définis)")
        return

    db: Session = SessionLocal()
    try:
        from .models import User, UserRole
        from .auth.security import hash_password, create_email_token
        from .email.service import send_admin_welcome_email

        existing = db.query(User).filter(
            User.role == UserRole.admin
        ).first()

        if existing:
            logger.info("bootstrap.admin_skipped (admin déjà existant)")
            return

        admin_user = User(
            email           = settings.admin_email.lower().strip(),
            hashed_password = hash_password(settings.admin_password),
            full_name       = settings.admin_full_name or "Admin",
            role            = UserRole.admin,
            is_active       = True,
            is_verified     = True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        logger.info(f"bootstrap.admin_created email={settings.admin_email}")

        # Email de bienvenue avec lien reset password
        try:
            token = create_email_token(admin_user.email, "reset")
            await send_admin_welcome_email(
                admin_user.email,
                admin_user.full_name or "Admin",
                token,
            )
            logger.info(
                f"bootstrap.admin_welcome_sent email={settings.admin_email}"
            )
        except Exception as mail_err:
            logger.warning(
                f"bootstrap.admin_welcome_failed: {mail_err} "
                "(compte créé mais email non envoyé)"
            )

    except Exception as e:
        db.rollback()
        logger.error(f"bootstrap.admin_error: {e}")
    finally:
        db.close()


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Créer l'admin par défaut si nécessaire
    await create_default_admin()

    # 2. Découvrir et enregistrer les applications agents
    #discover_and_register()

    # 3. Démarrer le scheduler de maintenance DB
    start_scheduler()

    logger.info("app.started")
    yield

    # Arrêt propre
    stop_scheduler()
    logger.info("app.stopped")


# ── Application FastAPI ───────────────────────────────────────────────────────

app = FastAPI(
    title       = "{{PROJECT_NAME}} API",
    version     = "0.1.0",
    lifespan    = lifespan,
    docs_url    = "/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url   = None,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Fichiers statiques (uploads médias)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS
origins = [
    "https://{{PROJECT_DOMAIN}}",
    "https://www.{{PROJECT_DOMAIN}}",
]
if os.getenv("ENVIRONMENT") != "production":
    origins.append("http://localhost:5173")
    origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins     = origins,
    allow_credentials = True,
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers     = ["Content-Type", "Authorization", "Accept"],
)

# Sécurité — détection d'intrusion
app.add_middleware(SecurityMiddleware)

# Tracking géographique
#app.add_middleware(TrackingMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(waitlist.router,      prefix="/api")
app.include_router(auth.router,          prefix="/api")
app.include_router(users.router,         prefix="/api")
app.include_router(admin.router,         prefix="/api")
app.include_router(onboarding.router,    prefix="/api")
app.include_router(content.router,       prefix="/api")
app.include_router(admin_content.router, prefix="/api")
app.include_router(media.router,         prefix="/api")
app.include_router(admin_db.router,      prefix="/api")
app.include_router(agent_services.router, prefix="/api")  # Services agentic IA
app.include_router(seo.router)                            # sans prefix — /sitemap.xml, /robots.txt
app.include_router(tracking.router,    prefix="/api")
app.include_router(analytics.router,   prefix="/api")
app.include_router(security_router.router, prefix="/api")
# Monetization — activated via env flags
app.include_router(shop_webhook.router,  prefix="/api")   # /api/shop/webhook (no auth — Stripe sig)
app.include_router(shop.router,          prefix="/api")   # /api/shop/…
app.include_router(subscription.router,  prefix="/api")   # /api/subscription/…
app.include_router(admin_shop.router,    prefix="/api")   # /api/admin/shop/…
# ── Health check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"health.check_failed: {e}")

    return {
        "status":   "ok" if db_status == "ok" else "degraded",
        "version":  app.version,
        "database": db_status,
    }