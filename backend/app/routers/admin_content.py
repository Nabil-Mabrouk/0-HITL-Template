"""
CRUD admin pour la gestion des tutoriaux et leçons.
Accessible uniquement aux admins.
"""

import logging
import io
import zipfile
import os
import uuid
import json
import aiofiles
import re
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile

# Dossier pour les médias
UPLOAD_DIR = "uploads"

# Types autorisés pour l'import
ALLOWED_MEDIA_TYPES = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".mp4", ".webm", ".mp3", ".pdf",
}

def make_slug(text: str) -> str:
    """Génère un slug depuis un texte."""
    if not text:
        return ""
    slug = text.lower().strip()
    slug = re.sub(r"[àáâãäå]", "a", slug)
    slug = re.sub(r"[èéêë]",   "e", slug)
    slug = re.sub(r"[ìíîï]",   "i", slug)
    slug = re.sub(r"[òóôõö]",  "o", slug)
    slug = re.sub(r"[ùúûü]",   "u", slug)
    slug = re.sub(r"[ç]",      "c", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug

from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Tutorial, Lesson, User
from app.schemas.content import (
    TutorialCreate, TutorialUpdate, TutorialResponse,
    LessonCreate, LessonUpdate, LessonResponse,
)
from app.auth.dependencies import require_admin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/content", tags=["admin-content"])


# ── Tutorials CRUD ────────────────────────────────────────────────────────────

@router.get("/tutorials")
async def list_all_tutorials(
    page:     int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db:       Session = Depends(get_db),
    admin:    User    = Depends(require_admin),
):
    """Liste tous les tutoriaux (publiés et brouillons)."""
    total = db.query(Tutorial).count()
    items = (
        db.query(Tutorial)
        .order_by(desc(Tutorial.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {"total": total, "page": page, "per_page": per_page,
            "tutorials": [TutorialResponse.model_validate(t) for t in items]}


@router.post("/tutorials", response_model=TutorialResponse,
             status_code=201)
async def create_tutorial(
    payload: TutorialCreate,
    db:      Session = Depends(get_db),
    admin:   User    = Depends(require_admin),
):
    # Vérifier l'unicité du slug
    if db.query(Tutorial).filter(Tutorial.slug == payload.slug).first():
        raise HTTPException(status_code=400,
                            detail="Ce slug est déjà utilisé")
    t = Tutorial(**payload.model_dump(), author_id=admin.id)
    db.add(t)
    db.commit()
    db.refresh(t)
    logger.info(f"content.tutorial.created id={t.id} by admin={admin.id}")
    return t


@router.get("/tutorials/{tutorial_id}", response_model=TutorialResponse)
async def get_tutorial_admin(
    tutorial_id: int,
    db:          Session = Depends(get_db),
    admin:       User    = Depends(require_admin),
):
    """Récupère les détails d'un tutorial spécifique."""
    t = db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tutorial introuvable")
    return t


@router.put("/tutorials/{tutorial_id}", response_model=TutorialResponse)
async def update_tutorial(
    tutorial_id: int,
    payload:     TutorialUpdate,
    db:          Session = Depends(get_db),
    admin:       User    = Depends(require_admin),
):
    tutorial = db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial introuvable")

    if payload.title        is not None: tutorial.title        = payload.title
    if payload.description  is not None: tutorial.description  = payload.description
    if payload.cover_image  is not None: tutorial.cover_image  = payload.cover_image
    if payload.access_role  is not None: tutorial.access_role  = payload.access_role
    if payload.is_published is not None: tutorial.is_published = payload.is_published
    if payload.lang         is not None: tutorial.lang         = payload.lang
    if payload.tags         is not None: tutorial.tags         = payload.tags
    if payload.is_featured  is not None:
        # Un seul tutorial featured à la fois
        if payload.is_featured:
            db.query(Tutorial).filter(
                Tutorial.id != tutorial_id
            ).update({"is_featured": False})
        tutorial.is_featured = payload.is_featured

    db.commit()
    db.refresh(tutorial)
    return tutorial


@router.delete("/tutorials/{tutorial_id}")
async def delete_tutorial(
    tutorial_id: int,
    db:          Session = Depends(get_db),
    admin:       User    = Depends(require_admin),
):
    t = db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tutorial introuvable")
    db.delete(t)
    db.commit()
    return {"message": "Tutorial supprimé"}


# ── Lessons CRUD ──────────────────────────────────────────────────────────────

@router.get("/tutorials/{tutorial_id}/lessons")
async def list_lessons(
    tutorial_id: int,
    db:          Session = Depends(get_db),
    admin:       User    = Depends(require_admin),
):
    lessons = (
        db.query(Lesson)
        .filter(Lesson.tutorial_id == tutorial_id)
        .order_by(Lesson.order)
        .all()
    )
    return [LessonResponse.model_validate(l) for l in lessons]


@router.post("/tutorials/{tutorial_id}/lessons",
             response_model=LessonResponse, status_code=201)
async def create_lesson(
    tutorial_id: int,
    payload:     LessonCreate,
    db:          Session = Depends(get_db),
    admin:       User    = Depends(require_admin),
):
    t = db.query(Tutorial).filter(Tutorial.id == tutorial_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Tutorial introuvable")

    # Vérifier unicité du slug dans le tutorial
    if db.query(Lesson).filter(
        Lesson.tutorial_id == tutorial_id,
        Lesson.slug == payload.slug,
    ).first():
        raise HTTPException(status_code=400,
                            detail="Ce slug est déjà utilisé dans ce tutorial")

    l = Lesson(**payload.model_dump(), tutorial_id=tutorial_id)
    db.add(l)
    db.commit()
    db.refresh(l)
    logger.info(f"content.lesson.created id={l.id} tutorial={tutorial_id}")
    return l


@router.put("/tutorials/{tutorial_id}/lessons/{lesson_id}",
            response_model=LessonResponse)
async def update_lesson(
    tutorial_id: int,
    lesson_id:   int,
    payload:     LessonUpdate,
    db:          Session = Depends(get_db),
    admin:       User    = Depends(require_admin),
):
    l = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.tutorial_id == tutorial_id,
    ).first()
    if not l:
        raise HTTPException(status_code=404, detail="Leçon introuvable")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(l, k, v)
    db.commit()
    db.refresh(l)
    return l


@router.delete("/tutorials/{tutorial_id}/lessons/{lesson_id}")
async def delete_lesson(
    tutorial_id: int,
    lesson_id:   int,
    db:          Session = Depends(get_db),
    admin:       User    = Depends(require_admin),
):
    l = db.query(Lesson).filter(
        Lesson.id == lesson_id,
        Lesson.tutorial_id == tutorial_id,
    ).first()
    if not l:
        raise HTTPException(status_code=404, detail="Leçon introuvable")
    db.delete(l)
    db.commit()
    return {"message": "Leçon supprimée"}


@router.put("/tutorials/{tutorial_id}/lessons/reorder")
async def reorder_lessons(
    tutorial_id: int,
    payload:     dict,
    db:          Session = Depends(get_db),
    admin:       User    = Depends(require_admin),
):
    """
    Réordonne les leçons.
    payload: { "order": [lesson_id, lesson_id, ...] }
    """
    order = payload.get("order", [])
    for i, lesson_id in enumerate(order):
        db.query(Lesson).filter(
            Lesson.id == lesson_id,
            Lesson.tutorial_id == tutorial_id,
        ).update({"order": i})
    db.commit()
    return {"message": "Ordre mis à jour"}

@router.post("/tutorials/import")
async def import_tutorial_zip(
    file:  UploadFile = File(...),
    db:    Session    = Depends(get_db),
    admin: User       = Depends(require_admin),
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400,
                            detail="Le fichier doit être un ZIP")

    content = await file.read()
    if len(content) > 500 * 1024 * 1024:
        raise HTTPException(status_code=400,
                            detail="Fichier trop volumineux (max 500MB)")

    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="ZIP invalide")

    names = zf.namelist()

    # ── Lire tutorial.json ────────────────────────────────────────────────
    if "tutorial.json" not in names:
        raise HTTPException(status_code=400,
                            detail="tutorial.json manquant")
    try:
        data = json.loads(zf.read("tutorial.json").decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400,
                            detail="tutorial.json invalide")

    for field in ["title", "slug"]:
        if field not in data:
            raise HTTPException(
                status_code=400,
                detail=f"Champ requis manquant dans tutorial.json : {field}"
            )

    # ── Lire les fichiers de leçons ───────────────────────────────────────
    lesson_files = sorted([
        n for n in names
        if n.startswith("lessons/") and n.endswith(".json")
    ])

    if not lesson_files:
        raise HTTPException(status_code=400,
                            detail="Aucun fichier leçon trouvé dans lessons/")

    lessons_data = []
    for lf in lesson_files:
        try:
            lesson = json.loads(zf.read(lf).decode("utf-8"))
            if "title" not in lesson:
                logger.warning(f"import.lesson.skipped missing title: {lf}")
                continue
            # Si pas de slug, générer depuis le titre
            if "slug" not in lesson:
                lesson["slug"] = make_slug(lesson["title"])
            lessons_data.append(lesson)
        except Exception as e:
            logger.warning(f"import.lesson.invalid {lf}: {e}")
            continue

    # ── Extraire les médias ───────────────────────────────────────────────
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    media_map: dict[str, str] = {}

    media_files = [
        n for n in names
        if n.startswith("media/") and not n.endswith("/")
    ]

    for media_path in media_files:
        filename = os.path.basename(media_path)
        ext      = os.path.splitext(filename)[1].lower()

        if ext not in ALLOWED_MEDIA_TYPES:
            logger.warning(f"import.media.skipped {filename}")
            continue

        unique_name = f"{uuid.uuid4().hex}{ext}"
        dest_path   = os.path.join(UPLOAD_DIR, unique_name)

        async with aiofiles.open(dest_path, "wb") as f:
            await f.write(zf.read(media_path))

        # Mapper les deux formes possibles dans le contenu
        media_map[media_path]          = f"/uploads/{unique_name}"
        media_map[f"media/{filename}"] = f"/uploads/{unique_name}"

    def replace_media_paths(text: str) -> str:
        if not text:
            return text
        for original, url in media_map.items():
            text = text.replace(original, url)
        return text

    # ── Créer ou remplacer le tutorial ────────────────────────────────────
    slug     = data["slug"]
    existing = db.query(Tutorial).filter(Tutorial.slug == slug).first()

    cover_image = data.get("cover_image")
    if cover_image and cover_image in media_map:
        cover_image = media_map[cover_image]

    if existing:
        db.query(Lesson).filter(
            Lesson.tutorial_id == existing.id
        ).delete()
        existing.title        = data["title"]
        existing.description  = data.get("description")
        existing.cover_image  = cover_image
        existing.access_role  = data.get("access_role", "user")
        existing.is_published = data.get("is_published", False)
        existing.author_id    = admin.id
        db.flush()
        tutorial = existing
        action   = "updated"
    else:
        tutorial = Tutorial(
            title        = data["title"],
            slug         = slug,
            description  = data.get("description"),
            cover_image  = cover_image,
            access_role  = data.get("access_role", "user"),
            is_published = data.get("is_published", False),
            author_id    = admin.id,
        )
        db.add(tutorial)
        db.flush()
        action = "created"

    # ── Créer les leçons ──────────────────────────────────────────────────
    # Trier par order si défini, sinon garder l'ordre des fichiers
    lessons_data.sort(key=lambda l: l.get("order", 999))

    for i, ld in enumerate(lessons_data):
        lesson = Lesson(
            tutorial_id      = tutorial.id,
            title            = ld["title"],
            slug             = ld["slug"],
            order            = ld.get("order", i),
            content          = replace_media_paths(ld.get("content", "")),
            duration_minutes = ld.get("duration_minutes"),
            is_published     = ld.get("is_published", False),
        )
        db.add(lesson)

    db.commit()
    db.refresh(tutorial)

    logger.info(
        f"import.tutorial.{action} slug={slug} "
        f"lessons={len(lessons_data)} media={len(media_map)} "
        f"by admin={admin.id}"
    )

    return {
        "message": f"Tutorial '{data['title']}' importé avec succès",
        "action":  action,
        "slug":    slug,
        "lessons": len(lessons_data),
        "media":   len(media_map),
    }