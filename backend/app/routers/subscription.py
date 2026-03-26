"""
Abonnements Stripe — modèle économique récurrent.
Activé via MONETIZATION_SUBSCRIPTION=true dans .env.

L'abonnement actif donne le rôle `premium` à l'utilisateur.
Le rôle est retiré automatiquement via les webhooks Stripe.

Endpoints :
  GET  /api/subscription/plans        — liste des plans disponibles
  GET  /api/subscription/status       — statut de l'abonnement courant
  POST /api/subscription/checkout     — créer une session Stripe Checkout
  POST /api/subscription/portal       — rediriger vers Stripe Customer Portal
  POST /api/subscription/cancel       — annuler l'abonnement (fin de période)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..auth.dependencies import get_verified_user
from ..config import get_settings
from ..database import get_db
from ..limiter import limiter
from ..models import Subscription, SubscriptionStatus, User, UserRole

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/subscription", tags=["subscription"])


def _require_subscription():
    if not settings.monetization_subscription:
        raise HTTPException(status_code=404, detail="Subscriptions not enabled")


def _stripe():
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payment not configured")
    stripe.api_key = settings.stripe_secret_key
    return stripe


# ── Plans ─────────────────────────────────────────────────────────────────────

@router.get("/plans")
def list_plans(db: Session = Depends(get_db)):
    """
    Liste les plans d'abonnement disponibles depuis Stripe.

    Retourne uniquement les prices actifs de type `recurring`.
    """
    _require_subscription()
    _stripe()

    try:
        prices = stripe.Price.list(active=True, type="recurring", limit=10)
        return [
            {
                "id":           p.id,
                "currency":     p.currency,
                "unit_amount":  p.unit_amount,
                "interval":     p.recurring.interval,
                "interval_count": p.recurring.interval_count,
                "product_name": (
                    stripe.Product.retrieve(p.product).name
                    if isinstance(p.product, str) else p.product.get("name", "")
                ),
            }
            for p in prices.data
        ]
    except stripe.error.StripeError as e:
        logger.error(f"subscription.list_plans_error: {e}")
        raise HTTPException(status_code=502, detail="Payment service error")


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status")
def subscription_status(
    current_user: User    = Depends(get_verified_user),
    db:           Session = Depends(get_db),
):
    """Retourne le statut de l'abonnement de l'utilisateur courant."""
    _require_subscription()

    sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not sub:
        return {"status": "none", "is_premium": False}

    return {
        "status":             sub.status.value,
        "is_premium":         sub.status in (
                                  SubscriptionStatus.active,
                                  SubscriptionStatus.trialing
                              ),
        "current_period_end": (
            sub.current_period_end.isoformat() if sub.current_period_end else None
        ),
        "trial_end":          (
            sub.trial_end.isoformat() if sub.trial_end else None
        ),
        "cancelled_at":       (
            sub.cancelled_at.isoformat() if sub.cancelled_at else None
        ),
        "stripe_price_id":    sub.stripe_price_id,
    }


# ── Checkout ──────────────────────────────────────────────────────────────────

@router.post("/checkout")
@limiter.limit("10/minute")
def create_subscription_checkout(
    body:         dict,
    request:      Request,
    current_user: User    = Depends(get_verified_user),
    db:           Session = Depends(get_db),
):
    """
    Crée une session Stripe Checkout pour s'abonner.

    Body: { "price_id": "price_…", "success_url": "…", "cancel_url": "…" }
    """
    _require_subscription()
    _stripe()

    import re
    price_id = body.get("price_id")
    if not price_id:
        raise HTTPException(status_code=422, detail="price_id required")
    # Validate Stripe price ID format to prevent parameter injection
    if not re.match(r"^price_[A-Za-z0-9]{6,}$", price_id):
        raise HTTPException(status_code=422, detail="Invalid price_id format")

    # Validate redirects — only same-origin to prevent open redirect
    raw_success = body.get("success_url") or f"{settings.frontend_url}/premium?subscribed=1"
    raw_cancel  = body.get("cancel_url")  or f"{settings.frontend_url}/premium"
    for url in (raw_success, raw_cancel):
        if not url.startswith(settings.frontend_url):
            raise HTTPException(
                status_code=422,
                detail="success_url and cancel_url must be within the application domain",
            )
    success_url = raw_success
    cancel_url  = raw_cancel

    # Check for existing active subscription
    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status.in_([SubscriptionStatus.active, SubscriptionStatus.trialing]),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already subscribed")

    params: dict = {
        "mode":        "subscription",
        "line_items":  [{"price": price_id, "quantity": 1}],
        "success_url": success_url + "&session_id={CHECKOUT_SESSION_ID}",
        "cancel_url":  cancel_url,
        "customer_email": current_user.email,
        "metadata": {"user_id": str(current_user.id)},
    }

    if settings.monetization_trial_days > 0:
        params["subscription_data"] = {
            "trial_period_days": settings.monetization_trial_days
        }

    # Re-use existing Stripe customer if we already have one
    existing_sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()
    if existing_sub and existing_sub.stripe_customer_id:
        params["customer"] = existing_sub.stripe_customer_id
        del params["customer_email"]

    try:
        session = stripe.checkout.Session.create(**params)
    except stripe.error.StripeError as e:
        logger.error(f"subscription.checkout_error: {e}")
        raise HTTPException(status_code=502, detail="Payment service error")

    return {"checkout_url": session.url, "session_id": session.id}


# ── Customer Portal ───────────────────────────────────────────────────────────

@router.post("/portal")
def customer_portal(
    body:         dict,
    current_user: User    = Depends(get_verified_user),
    db:           Session = Depends(get_db),
):
    """
    Génère un lien vers le Stripe Customer Portal.

    L'utilisateur peut gérer son abonnement (changer de plan, annuler,
    mettre à jour sa carte bancaire) depuis ce portail Stripe.

    Body: { "return_url": "…" }  (optionnel)
    """
    _require_subscription()
    _stripe()

    sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=404, detail="No active subscription found")

    raw_return = body.get("return_url") or f"{settings.frontend_url}/profile"
    # Validate return_url to prevent open redirect attacks
    if not raw_return.startswith(settings.frontend_url):
        raise HTTPException(
            status_code=422,
            detail="return_url must be within the application domain",
        )

    try:
        session = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=raw_return,
        )
    except stripe.error.StripeError as e:
        logger.error(f"subscription.portal_error: {e}")
        raise HTTPException(status_code=502, detail="Payment service error")

    return {"portal_url": session.url}


# ── Cancel ────────────────────────────────────────────────────────────────────

@router.post("/cancel")
def cancel_subscription(
    current_user: User    = Depends(get_verified_user),
    db:           Session = Depends(get_db),
):
    """
    Annule l'abonnement à la fin de la période en cours.

    L'utilisateur garde l'accès premium jusqu'à current_period_end.
    Le webhook customer.subscription.deleted mettra à jour le rôle.
    """
    _require_subscription()
    _stripe()

    sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status.in_([SubscriptionStatus.active, SubscriptionStatus.trialing]),
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription")

    try:
        stripe.Subscription.modify(
            sub.stripe_subscription_id,
            cancel_at_period_end=True,
        )
    except stripe.error.StripeError as e:
        logger.error(f"subscription.cancel_error: {e}")
        raise HTTPException(status_code=502, detail="Payment service error")

    sub.cancelled_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        f"subscription.cancelled user_id={current_user.id} "
        f"sub_id={sub.stripe_subscription_id}"
    )

    return {
        "message":            "Subscription will cancel at period end",
        "current_period_end": (
            sub.current_period_end.isoformat() if sub.current_period_end else None
        ),
    }
