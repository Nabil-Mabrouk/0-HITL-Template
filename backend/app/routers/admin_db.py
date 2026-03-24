"""
Endpoints de maintenance de la base de données.

- Export/Import utilisateurs en ZIP
- Export bulk des tutoriaux
- Nettoyage automatique
- Stats et état de la DB
"""

import csv
import io
import json
import logging
import os
import uuid
import zipfile
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin
from ..auth.security import hash_password
from ..config import get_settings
from ..database import get_db, SessionLocal
from ..email.service import send_verification_email
from ..auth.security import create_email_token
from ..models import (
    User, UserRole, Tutorial, Lesson, RefreshToken,
    ActivityLog, Visit,
)

logger   = logging.getLogger(__name__)
router   = APIRouter(prefix="/admin/db", tags=["admin-db"])
settings = get_settings()

EXPORT_FIELDS = [
    "email", "full_name", "role", "is_active",
    "is_verified", "created_at",
]

from ..models import DbSettings, WaitlistEntry, UserProfile
from ..services.cleanup import run_cleanup, get_or_create_settings
from ..scheduler import schedule_cleanup


@router.get("/stats")
async def get_db_stats(
    db:    Session = Depends(get_db),
    admin: User    = Depends(require_admin),
):
    """
    Retourne les statistiques de la base de données :
    nombre de lignes par table et taille totale.
    """
    tables = {
        "users":          User,
        "waitlist":       WaitlistEntry,
        "tutorials":      Tutorial,
        "lessons":        Lesson,
        "refresh_tokens": RefreshToken,
        "activity_logs":  ActivityLog,
        "visits":         Visit,
    }

    counts = {}
    for name, model in tables.items():
        try:
            counts[name] = db.query(func.count(model.id)).scalar()
        except Exception:
            counts[name] = 0

    # Taille de la DB PostgreSQL
    try:
        size_result = db.execute(
            text("SELECT pg_size_pretty(pg_database_size(current_database()))")
        ).fetchone()
        db_size = size_result[0] if size_result else "N/A"
    except Exception:
        db_size = "N/A"

    # Taille par table
    try:
        table_sizes = {}
        for table_name in tables.keys():
            result = db.execute(
                text(f"SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))")
            ).fetchone()
            table_sizes[table_name] = result[0] if result else "N/A"
    except Exception:
        table_sizes = {}

    # Dernière migration Alembic
    try:
        alembic_version = db.execute(
            text("SELECT version_num FROM alembic_version")
        ).fetchone()
        last_migration = alembic_version[0] if alembic_version else "N/A"
    except Exception:
        last_migration = "N/A"

    cfg = get_or_create_settings(db)

    return {
        "counts":         counts,
        "db_size":        db_size,
        "table_sizes":    table_sizes,
        "last_migration": last_migration,
        "settings": {
            "tokens_retention_days": cfg.tokens_retention_days,
            "visits_retention_days": cfg.visits_retention_days,
            "logs_retention_days":   cfg.logs_retention_days,
            "cleanup_frequency":     cfg.cleanup_frequency,
            "last_cleanup_at":       cfg.last_cleanup_at.isoformat()
                                     if cfg.last_cleanup_at else None,
        },
    }


@router.put("/settings")
async def update_db_settings(
    payload: dict,
    db:      Session = Depends(get_db),
    admin:   User    = Depends(require_admin),
):
    """Met à jour les paramètres de maintenance."""
    cfg = get_or_create_settings(db)

    valid_fields = [
        "tokens_retention_days", "visits_retention_days",
        "logs_retention_days",   "cleanup_frequency",
    ]
    valid_frequencies = ["daily", "weekly", "monthly", "disabled"]

    for field in valid_fields:
        if field in payload:
            value = payload[field]
            if field == "cleanup_frequency":
                if value not in valid_frequencies:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Fréquence invalide. Valeurs acceptées : {valid_frequencies}"
                    )
            elif isinstance(value, int) and value < 1:
                raise HTTPException(
                    status_code=400,
                    detail=f"{field} doit être >= 1"
                )
            setattr(cfg, field, value)

    db.commit()
    db.refresh(cfg)

    # Replanifier le scheduler avec les nouveaux paramètres
    schedule_cleanup()

    logger.info(f"db.settings.updated by={admin.email} payload={payload}")

    return {
        "message":               "Paramètres mis à jour",
        "tokens_retention_days": cfg.tokens_retention_days,
        "visits_retention_days": cfg.visits_retention_days,
        "logs_retention_days":   cfg.logs_retention_days,
        "cleanup_frequency":     cfg.cleanup_frequency,
    }


@router.post("/cleanup")
async def manual_cleanup(
    db:    Session = Depends(get_db),
    admin: User    = Depends(require_admin),
):
    """Déclenche un nettoyage manuel immédiat."""
    logger.info(f"db.cleanup.manual triggered by={admin.email}")
    result = run_cleanup(db)
    return result


@router.post("/vacuum")
async def vacuum_db(
    db:    Session = Depends(get_db),
    admin: User    = Depends(require_admin),
):
    """
    Exécute VACUUM ANALYZE sur toutes les tables.
    Récupère l'espace disque et met à jour les statistiques.
    """
    try:
        # VACUUM ne peut pas s'exécuter dans une transaction
        db.execute(text("COMMIT"))
        db.execute(text("VACUUM ANALYZE"))
        logger.info(f"db.vacuum.completed by={admin.email}")
        return {"message": "VACUUM ANALYZE exécuté avec succès"}
    except Exception as e:
        logger.error(f"db.vacuum.error: {e}")
        raise HTTPException(status_code=500,
                            detail=f"Erreur VACUUM : {str(e)}")

@router.get("/export/users")
async def export_users(
    db:    Session = Depends(get_db),
    admin: User    = Depends(require_admin),
):
    """
    Exporte tous les utilisateurs actifs dans un ZIP contenant :
    - export.json  : métadonnées de l'export
    - users.json   : liste des utilisateurs (sans mots de passe)
    - users.csv    : même données en CSV

    Les comptes supprimés (email deleted_*) sont exclus.
    """
    users = (
        db.query(User)
        .filter(~User.email.like("deleted_%@deleted.invalid"))
        .order_by(User.created_at)
        .all()
    )

    users_data = [
        {
            "email":       u.email,
            "full_name":   u.full_name,
            "role":        u.role.value,
            "is_active":   u.is_active,
            "is_verified": u.is_verified,
            "created_at":  u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]

    # Métadonnées
    export_meta = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_by": admin.email,
        "total_users": len(users_data),
        "format":      "1.0",
        "fields":      EXPORT_FIELDS,
    }

    # CSV en mémoire
    csv_buffer = io.StringIO()
    writer     = csv.DictWriter(csv_buffer, fieldnames=EXPORT_FIELDS)
    writer.writeheader()
    writer.writerows(users_data)
    csv_content = csv_buffer.getvalue()

    # ZIP en mémoire
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("export.json",
                    json.dumps(export_meta, ensure_ascii=False, indent=2))
        zf.writestr("users.json",
                    json.dumps(users_data, ensure_ascii=False, indent=2))
        zf.writestr("users.csv", csv_content)

    zip_buffer.seek(0)
    filename = f"users-export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"

    logger.info(f"db.export.users count={len(users_data)} by={admin.email}")

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@router.post("/import/users")
async def import_users(
    file:        UploadFile = File(...),
    send_emails: bool       = Query(True),
    db:          Session    = Depends(get_db),
    admin:       User       = Depends(require_admin),
):
    """
    Importe des utilisateurs depuis un ZIP exporté.

    Comportement :
    - Email existant -> mise à jour (rôle, is_active, full_name)
    - Email nouveau  -> création avec mot de passe temporaire
    - Les mots de passe existants ne sont jamais écrasés
    - Si send_emails=true, envoie un email de vérification
      aux nouveaux utilisateurs
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400,
                            detail="Le fichier doit être un ZIP")

    content = await file.read()
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="ZIP invalide")

    if "users.json" not in zf.namelist():
        raise HTTPException(status_code=400,
                            detail="users.json manquant dans le ZIP")

    try:
        users_data = json.loads(zf.read("users.json").decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="users.json invalide")

    if not isinstance(users_data, list):
        raise HTTPException(status_code=400,
                            detail="users.json doit être une liste")

    created = 0
    updated = 0
    skipped = 0
    errors  = []

    for u_data in users_data:
        email = u_data.get("email", "").lower().strip()
        if not email or "@" not in email:
            skipped += 1
            continue

        # Valider le rôle
        try:
            role = UserRole(u_data.get("role", "user"))
        except ValueError:
            role = UserRole.user

        existing = db.query(User).filter(User.email == email).first()

        if existing:
            # Mise à jour des champs non sensibles
            existing.full_name  = u_data.get("full_name") or existing.full_name
            existing.role       = role
            existing.is_active  = u_data.get("is_active", existing.is_active)
            updated += 1
        else:
            # Créer avec mot de passe temporaire aléatoire
            temp_password = uuid.uuid4().hex[:12] + "A1!"
            new_user = User(
                email           = email,
                hashed_password = hash_password(temp_password),
                full_name       = u_data.get("full_name"),
                role            = role,
                is_active       = u_data.get("is_active", True),
                is_verified     = False,
            )
            db.add(new_user)
            db.flush()

            if send_emails:
                try:
                    token = create_email_token(email, "verify")
                    await send_verification_email(
                        email,
                        u_data.get("full_name") or "Utilisateur",
                        token,
                    )
                except Exception as e:
                    errors.append(f"Email non envoyé à {email}: {str(e)}")

            created += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500,
                            detail=f"Erreur lors de l'import: {str(e)}")

    logger.info(
        f"db.import.users created={created} updated={updated} "
        f"skipped={skipped} by={admin.email}"
    )

    return {
        "message": f"Import terminé : {created} créés, {updated} mis à jour, {skipped} ignorés",
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors":  errors,
    }

@router.get("/export/tutorial/{tutorial_id}")
async def export_tutorial(
    tutorial_id: int,
    db:          Session = Depends(get_db),
    admin:       User    = Depends(require_admin),
):
    """
    Exporte un tutorial en ZIP dans le format d'import standard :
    - tutorial.json       : métadonnées
    - lessons/XX-slug.json: une leçon par fichier
    - media/              : médias référencés (si présents localement)
    """
    tutorial = db.query(Tutorial).filter(
        Tutorial.id == tutorial_id
    ).first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial introuvable")

    lessons = (
        db.query(Lesson)
        .filter(Lesson.tutorial_id == tutorial_id)
        .order_by(Lesson.order)
        .all()
    )

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:

        # tutorial.json
        tutorial_data = {
            "title":        tutorial.title,
            "slug":         tutorial.slug,
            "description":  tutorial.description,
            "cover_image":  tutorial.cover_image,
            "access_role":  tutorial.access_role.value
                            if hasattr(tutorial.access_role, "value")
                            else tutorial.access_role,
            "is_published": tutorial.is_published,
            "lang":         tutorial.lang,
        }
        zf.writestr("tutorial.json",
                    json.dumps(tutorial_data, ensure_ascii=False, indent=2))

        # Un fichier par leçon
        media_to_include = set()

        for lesson in lessons:
            lesson_data = {
                "title":            lesson.title,
                "slug":             lesson.slug,
                "order":            lesson.order,
                "duration_minutes": lesson.duration_minutes,
                "is_published":     lesson.is_published,
                "content":          lesson.content or "",
            }
            filename = f"lessons/{lesson.order:02d}-{lesson.slug}.json"
            zf.writestr(filename,
                        json.dumps(lesson_data, ensure_ascii=False, indent=2))

            # Détecter les médias locaux référencés dans le contenu
            if lesson.content:
                import re
                # Chercher les URLs /uploads/fichier.ext
                matches = re.findall(r'/uploads/([^)\s"\']+)', lesson.content)
                media_to_include.update(matches)

        # Inclure les médias locaux trouvés
        for media_filename in media_to_include:
            media_path = os.path.join("uploads", media_filename)
            if os.path.exists(media_path):
                with open(media_path, "rb") as f:
                    zf.writestr(f"media/{media_filename}", f.read())

    zip_buffer.seek(0)
    safe_slug = tutorial.slug.replace("/", "-")
    filename  = f"{safe_slug}.zip"

    logger.info(
        f"db.export.tutorial id={tutorial_id} slug={tutorial.slug} "
        f"lessons={len(lessons)} by={admin.email}"
    )

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/tutorials/bulk")
async def export_all_tutorials(
    db:    Session = Depends(get_db),
    admin: User    = Depends(require_admin),
):
    """
    Exporte tous les tutoriaux dans un seul ZIP.
    Chaque tutorial est un sous-dossier avec la même structure.
    """
    tutorials = db.query(Tutorial).order_by(Tutorial.created_at).all()

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:

        # Index général
        index = {
            "exported_at":     datetime.now(timezone.utc).isoformat(),
            "total_tutorials": len(tutorials),
            "tutorials": [
                {
                    "id":           t.id,
                    "slug":         t.slug,
                    "title":        t.title,
                    "lang":         t.lang,
                    "is_published": t.is_published,
                    "lessons":      len(t.lessons),
                }
                for t in tutorials
            ],
        }
        zf.writestr("index.json",
                    json.dumps(index, ensure_ascii=False, indent=2))

        # Un sous-dossier par tutorial
        for tutorial in tutorials:
            prefix = f"{tutorial.slug}/"

            tutorial_data = {
                "title":        tutorial.title,
                "slug":         tutorial.slug,
                "description":  tutorial.description,
                "cover_image":  tutorial.cover_image,
                "access_role":  tutorial.access_role.value
                                if hasattr(tutorial.access_role, "value")
                                else tutorial.access_role,
                "is_published": tutorial.is_published,
                "lang":         tutorial.lang,
            }
            zf.writestr(f"{prefix}tutorial.json",
                        json.dumps(tutorial_data, ensure_ascii=False, indent=2))

            for lesson in sorted(tutorial.lessons, key=lambda l: l.order):
                lesson_data = {
                    "title":            lesson.title,
                    "slug":             lesson.slug,
                    "order":            lesson.order,
                    "duration_minutes": lesson.duration_minutes,
                    "is_published":     lesson.is_published,
                    "content":          lesson.content or "",
                }
                fname = f"{prefix}lessons/{lesson.order:02d}-{lesson.slug}.json"
                zf.writestr(fname,
                            json.dumps(lesson_data, ensure_ascii=False, indent=2))

    zip_buffer.seek(0)
    date     = datetime.now().strftime("%Y%m%d")
    filename = f"tutorials-bulk-{date}.zip"

    logger.info(
        f"db.export.tutorials.bulk count={len(tutorials)} by={admin.email}"
    )

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )