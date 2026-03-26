"""
Administration de la boutique — gestion des produits, liste des ventes, MRR.

Endpoints :
  GET    /api/admin/shop/products          — liste tous les produits
  POST   /api/admin/shop/products          — créer un produit
  PUT    /api/admin/shop/products/{id}     — modifier un produit
  DELETE /api/admin/shop/products/{id}     — désactiver un produit
  GET    /api/admin/shop/purchases         — liste des achats
  GET    /api/admin/shop/subscriptions     — liste des abonnements
  GET    /api/admin/shop/stats             — MRR, total ventes, etc.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin
from ..config import get_settings
from ..database import get_db
from ..models import Product, Purchase, Subscription, SubscriptionStatus, User

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/admin/shop", tags=["admin-shop"])


# ── Products CRUD ─────────────────────────────────────────────────────────────

@router.get("/products")
def list_products(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_admin),
):
    products = db.query(Product).order_by(desc(Product.created_at)).all()
    return [_product_full(p) for p in products]


@router.post("/products", status_code=201)
def create_product(
    body: dict,
    db:   Session = Depends(get_db),
    _:    User    = Depends(require_admin),
):
    required = ("name", "slug", "price_cents")
    for field in required:
        if field not in body:
            raise HTTPException(status_code=422, detail=f"{field} required")

    if db.query(Product).filter(Product.slug == body["slug"]).first():
        raise HTTPException(status_code=409, detail="Slug already exists")

    product = Product(
        name            = body["name"],
        slug            = body["slug"],
        description     = body.get("description"),
        price_cents     = int(body["price_cents"]),
        currency        = body.get("currency", "eur"),
        stripe_price_id = body.get("stripe_price_id"),
        file_path       = body.get("file_path"),
        cover_image     = body.get("cover_image"),
        is_active       = body.get("is_active", True),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    logger.info(f"admin.product_created id={product.id} slug={product.slug}")
    return _product_full(product)


@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    body:       dict,
    db:         Session = Depends(get_db),
    _:          User    = Depends(require_admin),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    updatable = (
        "name", "description", "price_cents", "currency",
        "stripe_price_id", "file_path", "cover_image", "is_active"
    )
    for field in updatable:
        if field in body:
            setattr(product, field, body[field])

    db.commit()
    db.refresh(product)
    return _product_full(product)


@router.delete("/products/{product_id}")
def deactivate_product(
    product_id: int,
    db:         Session = Depends(get_db),
    _:          User    = Depends(require_admin),
):
    """Soft delete — désactive le produit sans supprimer les achats."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()
    return {"deactivated": product_id}


def _product_full(p: Product) -> dict:
    return {
        "id":              p.id,
        "name":            p.name,
        "slug":            p.slug,
        "description":     p.description,
        "price_cents":     p.price_cents,
        "currency":        p.currency,
        "stripe_price_id": p.stripe_price_id,
        "file_path":       p.file_path,
        "cover_image":     p.cover_image,
        "is_active":       p.is_active,
        "created_at":      p.created_at.isoformat() if p.created_at else None,
    }


# ── Purchases ─────────────────────────────────────────────────────────────────

@router.get("/purchases")
def list_purchases(
    page:     int           = Query(1, ge=1),
    per_page: int           = Query(50, ge=1, le=200),
    days:     int           = Query(30, ge=1, le=365),
    db:       Session       = Depends(get_db),
    _:        User          = Depends(require_admin),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = (
        db.query(Purchase)
        .filter(Purchase.fulfilled_at != None, Purchase.created_at >= since)
        .order_by(desc(Purchase.created_at))
    )
    total    = query.count()
    purchases = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "purchases": [
            {
                "id":               p.id,
                "email":            p.email,
                "product_name":     p.product.name if p.product else None,
                "amount_paid_cents": p.amount_paid_cents,
                "currency":         p.currency,
                "download_count":   p.download_count,
                "max_downloads":    p.max_downloads,
                "fulfilled_at":     p.fulfilled_at.isoformat() if p.fulfilled_at else None,
                "stripe_session_id": p.stripe_session_id,
            }
            for p in purchases
        ],
    }


# ── Subscriptions ─────────────────────────────────────────────────────────────

@router.get("/subscriptions")
def list_subscriptions(
    page:     int     = Query(1, ge=1),
    per_page: int     = Query(50, ge=1, le=200),
    status:   Optional[str] = Query(None),
    db:       Session = Depends(get_db),
    _:        User    = Depends(require_admin),
):
    query = db.query(Subscription).order_by(desc(Subscription.created_at))
    if status:
        query = query.filter(Subscription.status == status)

    total = query.count()
    subs  = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "subscriptions": [
            {
                "id":                     s.id,
                "user_id":                s.user_id,
                "user_email":             s.user.email if s.user else None,
                "stripe_subscription_id": s.stripe_subscription_id,
                "stripe_customer_id":     s.stripe_customer_id,
                "status":                 s.status.value,
                "stripe_price_id":        s.stripe_price_id,
                "current_period_end":     s.current_period_end.isoformat() if s.current_period_end else None,
                "trial_end":              s.trial_end.isoformat() if s.trial_end else None,
                "cancelled_at":           s.cancelled_at.isoformat() if s.cancelled_at else None,
                "created_at":             s.created_at.isoformat() if s.created_at else None,
            }
            for s in subs
        ],
    }


# ── Stats / MRR ───────────────────────────────────────────────────────────────

@router.get("/stats")
def shop_stats(
    db: Session = Depends(get_db),
    _:  User    = Depends(require_admin),
):
    """
    Résumé financier:
    - Total ventes one-time (tous les temps + 30 derniers jours)
    - MRR estimé (abonnements actifs × prix mensuel si disponible)
    - Abonnements actifs / trialing / annulés
    """
    now = datetime.now(timezone.utc)
    since_30d = now - timedelta(days=30)

    # One-time sales
    total_sales = (
        db.query(func.coalesce(func.sum(Purchase.amount_paid_cents), 0))
        .filter(Purchase.fulfilled_at != None)
        .scalar()
    )
    sales_30d = (
        db.query(func.coalesce(func.sum(Purchase.amount_paid_cents), 0))
        .filter(
            Purchase.fulfilled_at != None,
            Purchase.created_at >= since_30d,
        )
        .scalar()
    )
    purchases_count = (
        db.query(func.count(Purchase.id))
        .filter(Purchase.fulfilled_at != None)
        .scalar()
    )

    # Subscription breakdown
    active_count   = db.query(func.count(Subscription.id)).filter(Subscription.status == SubscriptionStatus.active).scalar()
    trialing_count = db.query(func.count(Subscription.id)).filter(Subscription.status == SubscriptionStatus.trialing).scalar()
    cancelled_count = db.query(func.count(Subscription.id)).filter(Subscription.status == SubscriptionStatus.cancelled).scalar()
    past_due_count = db.query(func.count(Subscription.id)).filter(Subscription.status == SubscriptionStatus.past_due).scalar()

    return {
        "sales": {
            "total_cents":      total_sales,
            "last_30d_cents":   sales_30d,
            "total_purchases":  purchases_count,
        },
        "subscriptions": {
            "active":    active_count,
            "trialing":  trialing_count,
            "cancelled": cancelled_count,
            "past_due":  past_due_count,
            "total":     active_count + trialing_count + cancelled_count + past_due_count,
        },
    }
