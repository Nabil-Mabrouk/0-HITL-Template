from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Optional
import re


def make_slug(title: str) -> str:
    """Génère un slug depuis un titre."""
    if not title:
        return ""
    slug = title.lower().strip()
    slug = re.sub(r"[àáâãäå]", "a", slug)
    slug = re.sub(r"[èéêë]",   "e", slug)
    slug = re.sub(r"[ìíîï]",   "i", slug)
    slug = re.sub(r"[òóôõö]",  "o", slug)
    slug = re.sub(r"[ùúûü]",   "u", slug)
    slug = re.sub(r"[ç]",      "c", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug


# ── LessonSummary — doit être défini AVANT TutorialResponse ──────────────────

class LessonSummary(BaseModel):
    id:               int
    title:            str
    slug:             str
    order:            int
    duration_minutes: Optional[int]
    is_published:     bool

    model_config = {"from_attributes": True}


# ── Tutorial ──────────────────────────────────────────────────────────────────

class TutorialCreate(BaseModel):
    title:        str
    slug:         Optional[str]  = None
    description:  Optional[str]  = None
    cover_image:  Optional[str]  = None
    access_role:  str            = "user"
    is_published: bool           = False
    lang:         str            = "fr"
    tags:         list[str]      = []
    is_featured:  bool           = False

    @model_validator(mode="after")
    def generate_slug(self) -> "TutorialCreate":
        if not self.slug and self.title:
            self.slug = make_slug(self.title)
        return self


class TutorialUpdate(BaseModel):
    title:        Optional[str]       = None
    description:  Optional[str]       = None
    cover_image:  Optional[str]       = None
    access_role:  Optional[str]       = None
    is_published: Optional[bool]      = None
    lang:         Optional[str]       = None
    tags:         Optional[list[str]] = None
    is_featured:  Optional[bool]      = None


class TutorialResponse(BaseModel):
    id:           int
    title:        str
    slug:         str
    description:  Optional[str]
    cover_image:  Optional[str]
    access_role:  str
    is_published: bool
    lang:         str
    tags:         list[str] = []
    is_featured:  bool      = False
    views_count:  int       = 0
    created_at:   datetime
    lessons:      list[LessonSummary] = []

    model_config = {"from_attributes": True}


# ── Lesson ────────────────────────────────────────────────────────────────────

class LessonCreate(BaseModel):
    title:            str
    slug:             Optional[str]  = None
    order:            int            = 0
    content:          Optional[str]  = None
    duration_minutes: Optional[int]  = None
    is_published:     bool           = False

    @model_validator(mode="after")
    def generate_slug(self) -> "LessonCreate":
        if not self.slug and self.title:
            self.slug = make_slug(self.title)
        return self


class LessonUpdate(BaseModel):
    title:            Optional[str]  = None
    order:            Optional[int]  = None
    content:          Optional[str]  = None
    duration_minutes: Optional[int]  = None
    is_published:     Optional[bool] = None


class LessonResponse(BaseModel):
    id:               int
    tutorial_id:      int
    title:            str
    slug:             str
    order:            int
    content:          Optional[str]
    duration_minutes: Optional[int]
    is_published:     bool
    created_at:       datetime
    updated_at:       datetime

    model_config = {"from_attributes": True}