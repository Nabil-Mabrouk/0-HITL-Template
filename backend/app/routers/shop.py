"""
Boutique de produits numériques — achat unique.
Activé via MONETIZATION_SHOP=true dans .env.

Endpoints :
  GET  /api/shop/products            — liste des produits actifs
  GET  /api/shop/products/{slug}     — détail d'un produit
  POST /api/shop/checkout            — créer une session Stripe Checkout
  GET  /api/shop/download/{token}    — télécharger un fichier acheté (lien sécurisé)
  GET  /api/shop/purchases           — mes achats (authentifié)
"""

import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..auth.dependencies import get_optional_user, get_verified_user
from ..config import get_settings
from ..database import get_db
from ..limiter import limiter
from ..models import Product, Purchase, User

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/shop", tags=["shop"])

# Allowed directory for downloadable product files
_PRODUCTS_ROOT = Path(os.environ.get("PRODUCTS_DIR", "/data/products")).resolve()

# Validate Stripe price ID format
_STRIPE_PRICE_RE = re.compile(r"^price_[A-Za-z0-9]{6,}")


def _validate_file_path(file_path: str) -> Path:
    """
    Resolve and validate that a product file path is within _PRODUCTS_ROOT.
    Raises HTTPException 422 if the path escapes the allowed directory.
    """
    resolved = Path(file_path).resolve()
    try:
        resolved.relative_to(_PRODUCTS_ROOT)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"file_path must be inside {_PRODUCTS_ROOT}",
        )
    return resolved


def _validate_return_url(url: str) -> str:
    """
    Ensure return_url is within our own frontend origin to prevent open redirects.
    Accepts only URLs that start with settings.frontend_url.
    """
    if not url.startswith(settings.frontend_url):
        raise HTTPException(
            status_code=422,
            detail="return_url must be within the application domain",
        )
    return url

# Guard: all endpoints return 404 if shop is disabled
def _require_shop():
    if not settings.monetization_shop:
        raise HTTPException(status_code=404, detail="Shop not enabled")


# ── Products ──────────────────────────────────────────────────────────────────

@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    """Liste des produits numériques actifs."""
    _require_shop()
    products = db.query(Product).filter(Product.is_active == True).all()
    return [_product_out(p) for p in products]


@router.get("/products/{slug}")
def get_product(slug: str, db: Session = Depends(get_db)):
    """Détail d'un produit."""
    _require_shop()
    p = db.query(Product).filter(Product.slug == slug, Product.is_active == True).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return _product_out(p)


def _product_out(p: Product) -> dict:
    return {
        "id":           p.id,
        "name":         p.name,
        "slug":         p.slug,
        "description":  p.description,
        "price_cents":  p.price_cents,
        "currency":     p.currency,
        "cover_image":  p.cover_image,
    }


# ── Checkout ──────────────────────────────────────────────────────────────────

@router.post("/checkout")
@limiter.limit("10/minute")
async def create_checkout(
    body:         dict,
    request:      Request,
    db:           Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Crée une session Stripe Checkout pour un achat unique.

    Body: { "product_slug": "mon-ebook", "success_url": "...", "cancel_url": "..." }
    """
    _require_shop()

    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payment not configured")

    slug = body.get("product_slug")
    if not slug:
        raise HTTPException(status_code=422, detail="product_slug required")

    product = db.query(Product).filter(
        Product.slug == slug, Product.is_active == True
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product.stripe_price_id:
        raise HTTPException(status_code=503, detail="Product not configured in Stripe")

    # Validate redirects — only allow same-origin URLs to prevent open redirect
    raw_success = body.get("success_url") or f"{settings.frontend_url}/shop/success"
    raw_cancel  = body.get("cancel_url")  or f"{settings.frontend_url}/shop"
    success_url = _validate_return_url(raw_success)
    cancel_url  = _validate_return_url(raw_cancel)

    # Create pending purchase record
    email = (current_user.email if current_user else body.get("email", ""))
    if not email:
        raise HTTPException(status_code=422, detail="email required for guest checkout")

    purchase = Purchase(
        user_id    = current_user.id if current_user else None,
        product_id = product.id,
        email      = email,
    )
    db.add(purchase)
    db.flush()  # get purchase.id before commit

    stripe.api_key = settings.stripe_secret_key

    session_params = {
        "mode": "payment",
        "line_items": [{"price": product.stripe_price_id, "quantity": 1}],
        "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url":  cancel_url,
        "customer_email": email if not current_user else None,
        "metadata": {
            "purchase_id": purchase.id,
            "product_id":  product.id,
            "user_id":     current_user.id if current_user else "",
        },
    }

    try:
        stripe_session = stripe.checkout.Session.create(**session_params)
    except stripe.error.StripeError as e:
        db.rollback()
        logger.error(f"shop.checkout_error: {e}")
        raise HTTPException(status_code=502, detail="Payment service error")

    purchase.stripe_session_id = stripe_session.id
    db.commit()

    return {
        "checkout_url": stripe_session.url,
        "session_id":   stripe_session.id,
    }


# ── Download ──────────────────────────────────────────────────────────────────

@router.get("/download/{token}")
def download_file(token: str, db: Session = Depends(get_db)):
    """
    Télécharge un fichier acheté via un token sécurisé.

    - Vérifie que le token existe et n'est pas expiré
    - Vérifie le nombre de téléchargements restants
    - Incrémente le compteur
    - Sert le fichier directement
    """
    _require_shop()

    purchase = db.query(Purchase).filter(Purchase.download_token == token).first()

    if not purchase or not purchase.fulfilled_at:
        raise HTTPException(status_code=404, detail="Invalid download link")

    now = datetime.now(timezone.utc)

    if purchase.token_expires_at and now > purchase.token_expires_at:
        raise HTTPException(status_code=410, detail="Download link expired")

    if purchase.download_count >= purchase.max_downloads:
        raise HTTPException(status_code=410, detail="Download limit reached")

    product = purchase.product
    if not product or not product.file_path:
        raise HTTPException(status_code=404, detail="File not found")

    # Resolve path and confirm it stays within the allowed products directory
    try:
        safe_path = _validate_file_path(product.file_path)
    except HTTPException:
        logger.error(
            f"shop.download_path_traversal purchase_id={purchase.id} "
            f"path={product.file_path}"
        )
        raise HTTPException(status_code=404, detail="File not found")

    if not safe_path.is_file():
        logger.error(f"shop.download_file_missing path={safe_path}")
        raise HTTPException(status_code=500, detail="File unavailable")

    purchase.download_count += 1
    db.commit()

    filename = safe_path.name
    logger.info(
        f"shop.download purchase_id={purchase.id} "
        f"count={purchase.download_count}/{purchase.max_downloads}"
    )

    return FileResponse(
        path=str(safe_path),
        filename=filename,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── My purchases ──────────────────────────────────────────────────────────────

@router.get("/purchases")
def my_purchases(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_verified_user),
):
    """Liste des achats de l'utilisateur connecté."""
    _require_shop()

    purchases = (
        db.query(Purchase)
        .filter(Purchase.user_id == current_user.id, Purchase.fulfilled_at != None)
        .order_by(Purchase.created_at.desc())
        .all()
    )

    now = datetime.now(timezone.utc)
    return [
        {
            "id":               p.id,
            "product_name":     p.product.name if p.product else "Unknown",
            "product_slug":     p.product.slug if p.product else None,
            "amount_paid":      p.amount_paid_cents,
            "currency":         p.currency,
            "fulfilled_at":     p.fulfilled_at.isoformat() if p.fulfilled_at else None,
            "download_url":     (
                f"/api/shop/download/{p.download_token}"
                if p.download_token and (
                    not p.token_expires_at or p.token_expires_at > now
                ) and p.download_count < p.max_downloads
                else None
            ),
            "downloads_left":   max(0, p.max_downloads - p.download_count),
            "link_expires_at":  (
                p.token_expires_at.isoformat() if p.token_expires_at else None
            ),
        }
        for p in purchases
    ]
