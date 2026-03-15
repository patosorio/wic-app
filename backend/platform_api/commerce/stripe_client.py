"""
Stripe client wrapper. All Stripe SDK calls go through this module.
Amounts are in Decimal; convert to cents for Stripe.
When DEV_SKIP_STRIPE=true, returns mock objects without calling Stripe.
"""

from decimal import Decimal
from typing import NamedTuple
from uuid import uuid4

from core.config import settings


class PaymentIntentResult(NamedTuple):
    """Result of create_payment_intent."""

    id: str
    client_secret: str
    status: str


class RefundResult(NamedTuple):
    """Result of issue_refund."""

    id: str
    status: str


def _use_mock_stripe() -> bool:
    """Whether to skip real Stripe and use mock responses."""
    return (
        settings.dev_skip_stripe
        or not settings.stripe_secret_key
        or not settings.stripe_webhook_secret
    )


def create_payment_intent(amount: Decimal, currency: str = "eur") -> PaymentIntentResult:
    """
    Create a Stripe PaymentIntent for immediate charge.
    Amount in Decimal (e.g. 19.99), converted to cents for Stripe.
    When DEV_SKIP_STRIPE=true, returns mock result without API call.
    """
    if _use_mock_stripe():
        pid = f"pi_dev_{uuid4().hex[:24]}"
        return PaymentIntentResult(
            id=pid,
            client_secret=f"{pid}_secret_dev_{uuid4().hex[:16]}",
            status="requires_payment_method",
        )

    import stripe

    stripe.api_key = settings.stripe_secret_key
    amount_cents = int(amount * 100)
    pi = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency,
        automatic_payment_methods={"enabled": True},
    )
    return PaymentIntentResult(
        id=pi.id,
        client_secret=pi.client_secret or "",
        status=pi.status or "unknown",
    )


def issue_refund(payment_intent_id: str) -> RefundResult:
    """
    Issue a full refund for a PaymentIntent.
    When DEV_SKIP_STRIPE=true, returns mock result without API call.
    """
    if _use_mock_stripe():
        return RefundResult(id=f"re_dev_{uuid4().hex[:24]}", status="succeeded")

    import stripe

    stripe.api_key = settings.stripe_secret_key
    refund = stripe.Refund.create(payment_intent=payment_intent_id)
    return RefundResult(id=refund.id, status=refund.status or "unknown")


def construct_webhook_event(payload: bytes, sig_header: str | None) -> dict | None:
    """
    Verify and parse Stripe webhook payload.
    Returns event dict or None if verification fails.
    When DEV_SKIP_STRIPE=true, accepts payload as raw JSON (no sig verification).
    """
    if _use_mock_stripe():
        import json

        return json.loads(payload)
    if not sig_header or not settings.stripe_webhook_secret:
        return None

    import stripe

    try:
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except Exception:
        return None
