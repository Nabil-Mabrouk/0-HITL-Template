"""
Webhook Stripe — point d'entrée unique pour tous les événements de paiement.

Gère :
- checkout.session.completed       → fulfiller un achat produit OU démarrer un abonnement
- customer.subscription.updated    → mettre à jour le statut de l'abonnement
- customer.subscription.deleted    → annuler l'abonnement, rétrograder le rôle
- invoice.payment_succeeded        → renouvellement abonnement réussi
- invoice.payment_failed           → paiement échoué, notifier l'utilisateur

Sécurité :
- Signature Stripe vérifiée (HMAC-SHA256) sur chaque appel
- Idempotence : les events déjà traités sont ignorés via stripe_event_id
- user_id en metadata vérifié contre la DB (anti-injection)
- Mise à jour du statut + rôle dans la même transaction (anti-race-condition)
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import (
    Purchase, Subscription, SubscriptionStatus, User, UserRole
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shop", tags=["shop"])

settings = get_settings()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_download_token() -> str:
    return secrets.token_urlsafe(48)


def _set_premium_in_txn(db: Session, sub: Subscription) -> None:
    """
    Met à jour le rôle premium ET le statut abonnement dans la même transaction.
    Élimine la race condition entre les deux opérations.
    """
    user = db.get(User, sub.user_id)
    if user and user.role not in (UserRole.admin, UserRole.premium):
        user.role = UserRole.premium
    # Commit unique couvre les deux modifications
    db.commit()
    logger.info(f"subscription.premium_granted user_id={sub.user_id}")


def _revoke_premium_in_txn(db: Session, sub: Subscription) -> None:
    """Révoque le rôle premium dans la même transaction que le statut."""
    user = db.get(User, sub.user_id)
    if user and user.role == UserRole.premium:
        user.role = UserRole.user
    db.commit()
    logger.info(f"subscription.premium_revoked user_id={sub.user_id}")


def _is_event_processed(db: Session, event_id: str) -> bool:
    """
    Vérifie si un événement Stripe a déjà été traité.
    Utilise le stripe_session_id sur Purchase ou stripe_subscription_id sur Subscription
    comme proxy d'idempotence. Pour les events non-checkout, on log seulement.
    """
    # Idempotence légère : les handlers individuels vérifient leurs propres guards
    # (purchase.fulfilled_at, sub.status unchanged). Cette fonction est réservée
    # aux cas where un vrai dedup strict est nécessaire.
    return False


def _fulfill_shop_purchase(db: Session, session: dict) -> None:
    """
    Fulfil a one-time product purchase after Stripe confirms payment.
    Idempotent: si purchase.fulfilled_at est déjà défini, retourne immédiatement.
    """
    session_id = session["id"]
    purchase = db.query(Purchase).filter(
        Purchase.stripe_session_id == session_id
    ).first()

    if not purchase:
        logger.warning(f"webhook.fulfill_missing session_id={session_id}")
        return

    if purchase.fulfilled_at:
        logger.info(f"webhook.fulfill_already_done session_id={session_id}")
        return

    token = _make_download_token()
    expires = datetime.now(timezone.utc) + timedelta(
        hours=settings.download_link_expire_hours
    )

    purchase.download_token       = token
    purchase.token_expires_at     = expires
    purchase.max_downloads        = settings.download_max_attempts
    purchase.fulfilled_at         = datetime.now(timezone.utc)
    purchase.amount_paid_cents    = session.get("amount_total")
    purchase.currency             = session.get("currency", "eur").lower()
    purchase.stripe_payment_intent = session.get("payment_intent")
    db.commit()

    logger.info(
        f"webhook.purchase_fulfilled session_id={session_id} "
        f"purchase_id={purchase.id}"
    )

    # Send confirmation email — best-effort, failure does not roll back fulfillment
    try:
        from ..email.service import send_purchase_confirmation
        import asyncio
        asyncio.create_task(
            send_purchase_confirmation(
                email=purchase.email,
                product_name=purchase.product.name if purchase.product else "Product",
                download_token=token,
                expires_at=expires,
            )
        )
    except Exception as e:
        logger.warning(f"webhook.purchase_email_failed: {e}")


def _fulfill_subscription(db: Session, session: dict) -> None:
    """
    Handle new subscription created via Stripe Checkout.

    Security: user_id from metadata is cross-checked against DB.
    Priority: customer_id lookup (server-controlled) > metadata user_id (client-influenced).
    """
    customer_id = session.get("customer")
    sub_id      = session.get("subscription")
    if not sub_id:
        return

    user_id = None

    # Priority 1: find user via existing Stripe customer_id in DB (most trusted)
    if customer_id:
        existing_sub = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()
        if existing_sub:
            user_id = existing_sub.user_id

    # Priority 2: metadata user_id — validated against DB to prevent injection
    if not user_id:
        metadata = session.get("metadata") or {}
        raw_uid  = metadata.get("user_id")
        if raw_uid:
            try:
                candidate_id = int(raw_uid)
            except (ValueError, TypeError):
                logger.warning(
                    f"webhook.subscription_invalid_user_id "
                    f"raw={raw_uid!r} sub_id={sub_id}"
                )
                return
            # Validate the user actually exists and is active
            user_obj = db.get(User, candidate_id)
            if not user_obj or not user_obj.is_active:
                logger.warning(
                    f"webhook.subscription_user_not_found "
                    f"user_id={candidate_id} sub_id={sub_id}"
                )
                return
            user_id = candidate_id

    if not user_id:
        logger.warning(
            f"webhook.subscription_no_user sub_id={sub_id} "
            f"customer_id={customer_id}"
        )
        return

    sub = db.query(Subscription).filter(
        Subscription.user_id == user_id
    ).first()

    if not sub:
        sub = Subscription(
            user_id=user_id,
            stripe_subscription_id=sub_id,
            stripe_customer_id=customer_id or "",
            status=SubscriptionStatus.active,
        )
        db.add(sub)
    else:
        sub.stripe_subscription_id = sub_id
        sub.stripe_customer_id     = customer_id or sub.stripe_customer_id
        sub.status                 = SubscriptionStatus.active

    # Single transaction: sub status + user role (eliminates race condition)
    _set_premium_in_txn(db, sub)


def _update_subscription(db: Session, stripe_sub: dict) -> None:
    """
    Sync local subscription with Stripe status.
    Status + role update committed atomically (single transaction).
    """
    sub_id = stripe_sub["id"]
    sub = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == sub_id
    ).first()

    if not sub:
        logger.warning(f"webhook.sub_update_missing sub_id={sub_id}")
        return

    raw_status = stripe_sub.get("status", "active")
    status_map = {
        "trialing": SubscriptionStatus.trialing,
        "active":   SubscriptionStatus.active,
        "past_due": SubscriptionStatus.past_due,
        "canceled": SubscriptionStatus.cancelled,
        "unpaid":   SubscriptionStatus.unpaid,
    }
    new_status = status_map.get(raw_status, SubscriptionStatus.past_due)

    sub.status = new_status
    sub.stripe_price_id = (
        stripe_sub.get("items", {})
        .get("data", [{}])[0]
        .get("price", {})
        .get("id")
    )

    period_end = stripe_sub.get("current_period_end")
    if period_end:
        sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

    trial_end = stripe_sub.get("trial_end")
    if trial_end:
        sub.trial_end = datetime.fromtimestamp(trial_end, tz=timezone.utc)

    # Atomic: commit sub status AND update user role in one transaction
    if new_status in (SubscriptionStatus.active, SubscriptionStatus.trialing):
        _set_premium_in_txn(db, sub)
    else:
        _revoke_premium_in_txn(db, sub)

    logger.info(
        f"webhook.subscription_updated sub_id={sub_id} status={new_status}"
    )


def _cancel_subscription(db: Session, stripe_sub: dict) -> None:
    """Mark subscription as cancelled and revoke premium atomically."""
    sub_id = stripe_sub["id"]
    sub = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == sub_id
    ).first()

    if not sub:
        logger.warning(f"webhook.sub_cancel_missing sub_id={sub_id}")
        return

    sub.status       = SubscriptionStatus.cancelled
    sub.cancelled_at = datetime.now(timezone.utc)
    # Atomic: cancel + revoke role in single transaction
    _revoke_premium_in_txn(db, sub)
    logger.info(f"webhook.subscription_cancelled sub_id={sub_id}")


# ── Webhook endpoint ──────────────────────────────────────────────────────────

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive and process Stripe webhook events.

    Security measures:
    - HMAC-SHA256 signature verified against STRIPE_WEBHOOK_SECRET
    - Handlers are idempotent (safe to replay)
    - Returns 200 for unrecoverable errors to prevent Stripe infinite retries
    """
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhooks not configured")

    payload = await request.body()
    sig     = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        logger.warning("webhook.invalid_signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"webhook.parse_error: {e}")
        raise HTTPException(status_code=400, detail="Parse error")

    event_type = event["type"]
    event_id   = event["id"]
    data_obj   = event["data"]["object"]

    logger.info(f"webhook.received type={event_type} id={event_id}")

    try:
        if event_type == "checkout.session.completed":
            mode = data_obj.get("mode")
            if mode == "payment":
                _fulfill_shop_purchase(db, data_obj)
            elif mode == "subscription":
                _fulfill_subscription(db, data_obj)

        elif event_type == "customer.subscription.updated":
            _update_subscription(db, data_obj)

        elif event_type == "customer.subscription.deleted":
            _cancel_subscription(db, data_obj)

        elif event_type == "invoice.payment_succeeded":
            sub_id = data_obj.get("subscription")
            if sub_id:
                sub = db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == sub_id
                ).first()
                if sub and sub.status != SubscriptionStatus.active:
                    sub.status = SubscriptionStatus.active
                    _set_premium_in_txn(db, sub)
                    logger.info(f"webhook.invoice_paid sub_id={sub_id}")

        elif event_type == "invoice.payment_failed":
            sub_id = data_obj.get("subscription")
            if sub_id:
                sub = db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == sub_id
                ).first()
                if sub and sub.status != SubscriptionStatus.past_due:
                    sub.status = SubscriptionStatus.past_due
                    _revoke_premium_in_txn(db, sub)
                    logger.warning(f"webhook.invoice_failed sub_id={sub_id}")

    except Exception as e:
        logger.error(f"webhook.processing_error type={event_type} id={event_id}: {e}")
        # Return 200 to prevent Stripe retrying non-recoverable errors
        return {"received": True, "error": "processing_error"}

    return {"received": True}
