"""
Endpoints SEO — sitemap.xml et robots.txt.
Montés sans préfixe /api pour être accessibles à la racine.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Tutorial
from app.config import get_settings

router   = APIRouter(tags=["seo"])
settings = get_settings()


@router.get("/sitemap.xml", response_class=Response)
async def sitemap(db: Session = Depends(get_db)):
    base = settings.frontend_url

    static_urls = [
        {"loc": base,             "priority": "1.0", "changefreq": "weekly"},
        {"loc": f"{base}/learn",  "priority": "0.9", "changefreq": "daily"},
    ]

    tutorials = db.query(Tutorial)\
                  .filter(Tutorial.is_published == True).all()

    tutorial_urls = []
    for t in tutorials:
        tutorial_urls.append({
            "loc":        f"{base}/learn/{t.slug}",
            "lastmod":    t.updated_at.strftime("%Y-%m-%d"),
            "priority":   "0.8",
            "changefreq": "weekly",
        })
        for l in t.lessons:
            if l.is_published:
                tutorial_urls.append({
                    "loc":        f"{base}/learn/{t.slug}/{l.slug}",
                    "lastmod":    l.updated_at.strftime("%Y-%m-%d"),
                    "priority":   "0.7",
                    "changefreq": "monthly",
                })

    all_urls = static_urls + tutorial_urls

    urls_xml = "\n".join([
        f"""  <url>
    <loc>{u["loc"]}</loc>
    {"<lastmod>" + u["lastmod"] + "</lastmod>" if "lastmod" in u else ""}
    <changefreq>{u.get("changefreq", "monthly")}</changefreq>
    <priority>{u.get("priority", "0.5")}</priority>
  </url>"""
        for u in all_urls
    ])

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}
</urlset>"""

    return Response(content=xml, media_type="application/xml")


@router.get("/robots.txt", response_class=Response)
async def robots():
    base = settings.frontend_url
    disallow_list = settings.robots_disallow_paths.split(",")
    disallow = "\n".join([
        f"Disallow: {p.strip()}"
        for p in disallow_list
    ])

    if not settings.robots_allow_indexing:
        content = "User-agent: *\nDisallow: /\n"
    else:
        content = f"User-agent: *\n{disallow}\n\nSitemap: {base}/sitemap.xml\n"

    return Response(content=content, media_type="text/plain")


@router.get("/llms.txt", response_class=Response)
async def llms(db: Session = Depends(get_db)):
    """
    LLM crawler guidance file (https://llmstxt.org).
    Lists public content, restricted areas, and do-not-index paths.
    """
    base     = settings.frontend_url
    tutorials = db.query(Tutorial)\
                  .filter(Tutorial.is_published == True,
                          Tutorial.access_role == "user").all()

    tutorial_lines = "\n".join(
        f"- [{t.title}]({base}/learn/{t.slug}): {t.description or ''}"
        for t in tutorials
    )

    content = f"""# llms.txt — AI crawler guidance

> {settings.project_name}

## Public content

- [Home]({base}/): Platform overview
- [Learn]({base}/learn): Tutorial catalogue
{tutorial_lines}

## Restricted content (requires authentication)

- [Profile]({base}/profile): User account
- [Admin]({base}/admin): Administration

## Do not index

- {base}/api/*
- {base}/admin/*
- {base}/profile/*
"""
    return Response(content=content, media_type="text/plain")
