"""
Endpoints publics pour la lecture du contenu.

Contrôle d'accès par rôle :
- Anonyme          : voit le catalogue user uniquement
- User             : voit user + aperçu premium (sans contenu)
- Premium / Admin  : voit et accède à tout
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Tutorial, Lesson, AccessRole, UserRole, User
from app.schemas.content import TutorialResponse, LessonResponse
from app.auth.dependencies import get_optional_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/content", tags=["content"])


def _user_can_access(tutorial: Tutorial, current_user: User | None) -> bool:
    """Retourne True si l'utilisateur peut accéder au contenu du tutorial."""
    if tutorial.access_role == AccessRole.admin:
        # Réservé aux admins uniquement
        return current_user is not None and current_user.role == UserRole.admin

    if tutorial.access_role == AccessRole.premium:
        if not current_user:
            return False
        return current_user.role in (UserRole.premium, UserRole.admin)

    # access_role == user
    if current_user and not current_user.is_active:
        return False
    return True


def _check_access(tutorial: Tutorial, current_user: User | None):
    """Lève une HTTPException si l'accès est refusé."""
    if not tutorial.is_published:
        raise HTTPException(status_code=404, detail="Tutorial introuvable")

    if not _user_can_access(tutorial, current_user):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Connexion requise pour accéder à ce contenu",
            )
        if current_user.role not in (UserRole.premium, UserRole.admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Contenu réservé aux membres Premium",
            )
        raise HTTPException(status_code=403, detail="Accès refusé")


@router.get("/tutorials", response_model=list[TutorialResponse])
async def list_tutorials(
    lang:         str | None  = Query(None),
    db:           Session     = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """
    Catalogue des tutoriaux publiés.

    - Anonyme         : uniquement les tutoriaux access_role="user"
    - User            : uniquement les tutoriaux access_role="user"
    - Premium         : tutoriaux access_role="user" + access_role="premium"
    - Admin           : tous les tutoriaux publiés (user, premium, admin)
    """
    query = db.query(Tutorial).filter(Tutorial.is_published == True)

    if lang:
        query = query.filter(Tutorial.lang == lang)

    # Restreindre le catalogue selon le rôle
    role = current_user.role if current_user else None

    if role == UserRole.admin:
        # Admin voit tout
        pass
    elif role == UserRole.premium:
        # Premium voit user + premium
        query = query.filter(
            Tutorial.access_role.in_([AccessRole.user, AccessRole.premium])
        )
    else:
        # User/anonyme voit seulement user
        query = query.filter(Tutorial.access_role == AccessRole.user)

    return query.order_by(Tutorial.created_at.desc()).all()


@router.get("/tutorials/{slug}", response_model=TutorialResponse)
async def get_tutorial(
    slug:         str,
    db:           Session     = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    tutorial = db.query(Tutorial).filter(Tutorial.slug == slug).first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial introuvable")
    _check_access(tutorial, current_user)

    # Incrémenter le compteur de vues
    tutorial.views_count = (tutorial.views_count or 0) + 1
    db.commit()
    db.refresh(tutorial)

    return tutorial


@router.get("/tutorials/{slug}/{lesson_slug}", response_model=LessonResponse)
async def get_lesson(
    slug:         str,
    lesson_slug:  str,
    db:           Session     = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """
    Contenu d'une leçon.
    Vérifie l'accès au tutorial parent avant de retourner la leçon.
    """
    tutorial = db.query(Tutorial).filter(Tutorial.slug == slug).first()
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial introuvable")

    _check_access(tutorial, current_user)

    lesson = (
        db.query(Lesson)
        .filter(
            Lesson.tutorial_id  == tutorial.id,
            Lesson.slug         == lesson_slug,
            Lesson.is_published == True,
        )
        .first()
    )
    if not lesson:
        raise HTTPException(status_code=404, detail="Leçon introuvable")

    logger.info(
        f"content.lesson.read slug={slug} lesson={lesson_slug} "
        f"user={current_user.id if current_user else 'anonymous'} "
        f"content_len={len(lesson.content) if lesson.content else 0}"
    )

    return lesson

@router.get("/tutorials-featured", response_model=TutorialResponse | None)
async def get_featured_tutorial(
    lang:         str | None  = Query(None),
    db:           Session     = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """Retourne le tutorial mis en avant (is_featured=True)."""
    query = db.query(Tutorial).filter(
        Tutorial.is_published == True,
        Tutorial.is_featured  == True,
    )
    if lang:
        query = query.filter(Tutorial.lang == lang)

    # Visibilité selon rôle
    role = current_user.role if current_user else None

    if role == UserRole.admin:
        pass
    elif role == UserRole.premium:
        query = query.filter(
            Tutorial.access_role.in_([AccessRole.user, AccessRole.premium])
        )
    else:
        query = query.filter(Tutorial.access_role == AccessRole.user)

    return query.first()


@router.get("/tutorials-popular", response_model=list[TutorialResponse])
async def get_popular_tutorials(
    lang:         str | None  = Query(None),
    limit:        int         = Query(6, ge=1, le=20),
    db:           Session     = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """Retourne les tutoriaux les plus vus."""
    query = db.query(Tutorial).filter(Tutorial.is_published == True)

    if lang:
        query = query.filter(Tutorial.lang == lang)

    role = current_user.role if current_user else None

    if role == UserRole.admin:
        pass
    elif role == UserRole.premium:
        query = query.filter(
            Tutorial.access_role.in_([AccessRole.user, AccessRole.premium])
        )
    else:
        query = query.filter(Tutorial.access_role == AccessRole.user)

    return query.order_by(Tutorial.views_count.desc()).limit(limit).all()


@router.get("/tutorials-recent", response_model=list[TutorialResponse])
async def get_recent_tutorials(
    lang:         str | None  = Query(None),
    limit:        int         = Query(6, ge=1, le=20),
    db:           Session     = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """Retourne les tutoriaux les plus récents."""
    query = db.query(Tutorial).filter(Tutorial.is_published == True)

    if lang:
        query = query.filter(Tutorial.lang == lang)

    role = current_user.role if current_user else None

    if role == UserRole.admin:
        pass
    elif role == UserRole.premium:
        query = query.filter(
            Tutorial.access_role.in_([AccessRole.user, AccessRole.premium])
        )
    else:
        query = query.filter(Tutorial.access_role == AccessRole.user)

    return query.order_by(Tutorial.created_at.desc()).limit(limit).all()

@router.get("/tutorials-search", response_model=list[TutorialResponse])
async def search_tutorials(
    q:            str         = Query(..., min_length=2),
    lang:         str | None  = Query(None),
    tag:          str | None  = Query(None),
    db:           Session     = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """Recherche dans le titre et la description. Filtre optionnel par tag."""
    from sqlalchemy import or_, cast, String

    query = db.query(Tutorial).filter(Tutorial.is_published == True)

    if lang:
        query = query.filter(Tutorial.lang == lang)

    role = current_user.role if current_user else None

    if role == UserRole.admin:
        pass
    elif role == UserRole.premium:
        query = query.filter(
            Tutorial.access_role.in_([AccessRole.user, AccessRole.premium])
        )
    else:
        query = query.filter(Tutorial.access_role == AccessRole.user)

    # Recherche texte dans titre et description
    search = f"%{q.lower()}%"
    query = query.filter(
        or_(
            Tutorial.title.ilike(search),
            Tutorial.description.ilike(search),
        )
    )

    # Filtre par tag (JSON contains)
    if tag:
        query = query.filter(
            cast(Tutorial.tags, String).ilike(f"%{tag}%")
        )

    return query.order_by(Tutorial.created_at.desc()).limit(20).all()