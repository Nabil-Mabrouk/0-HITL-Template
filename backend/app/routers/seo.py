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
        content = f"""User-agent: *
Allow: /
{disallow}

Sitemap: {base}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")
