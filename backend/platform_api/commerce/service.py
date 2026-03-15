"""Commerce service: order creation, webhook handling, refunds."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.events import publish_campaign_presale_incremented
from core.exceptions import CampaignNotActiveError, InsufficientCapacityError
from core.firestore import write_campaign_projection

from platform_api.campaigns.constants import CAMPAIGN_MAX_CAPACITY, PRESALE_PRICE_EUR
from platform_api.campaigns.models import Campaign, CampaignStatus
from platform_api.campaigns.service import get_campaign, increment_counter
from platform_api.commerce.models import Order, OrderStatus, PaymentEvent
from platform_api.commerce.stripe_client import create_payment_intent

logger = logging.getLogger(__name__)


def _campaign_projection_data(campaign: Campaign) -> dict:
    """Build Firestore projection dict for campaign."""
    from datetime import datetime, timezone

    percentage = (
        round(float(campaign.current_count / campaign.target * 100), 1)
        if campaign.target
        else 0
    )
    days_remaining = 0
    if campaign.ends_at:
        delta = campaign.ends_at - datetime.now(timezone.utc)
        days_remaining = max(0, delta.days)

    return {
        "release_id": str(campaign.release_id),
        "status": campaign.status.value,
        "current_count": campaign.current_count,
        "target": campaign.target,
        "percentage": percentage,
        "days_remaining": days_remaining,
        "presale_price": float(campaign.presale_price),
        "ends_at": campaign.ends_at.isoformat() if campaign.ends_at else None,
    }


async def create_order(
    campaign_id: UUID, customer_id: UUID, db: AsyncSession
) -> tuple[Order, str]:
    """
    Create pre-order: verify campaign ACTIVE, capacity, create PaymentIntent, create Order.
    When DEV_SKIP_STRIPE=true, also simulates payment success (increment counter, Firestore).
    """
    campaign = await get_campaign(campaign_id, db)
    if not campaign:
        raise ValueError("Campaign not found")
    if campaign.status != CampaignStatus.ACTIVE:
        raise CampaignNotActiveError(f"Campaign must be ACTIVE to pre-order, got {campaign.status}")
    if campaign.current_count >= CAMPAIGN_MAX_CAPACITY:
        raise InsufficientCapacityError("Campaign has reached maximum capacity")

    amount = PRESALE_PRICE_EUR
    pi = create_payment_intent(amount)

    order = Order(
        campaign_id=campaign_id,
        customer_id=customer_id,
        status=OrderStatus.PENDING_CAMPAIGN,
        amount=amount,
        stripe_payment_intent_id=pi.id,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    if settings.dev_skip_stripe:
        await _simulate_payment_success(order, db)

    return order, pi.client_secret


async def _simulate_payment_success(order: Order, db: AsyncSession) -> None:
    """
    When DEV_SKIP_STRIPE, simulate webhook payment_intent.succeeded flow.
    Inserts PaymentEvent, increments campaign counter, writes Firestore, publishes event.
    """
    stripe_event_id = f"evt_dev_{order.id}"
    existing = await db.execute(
        select(PaymentEvent).where(PaymentEvent.stripe_event_id == stripe_event_id)
    )
    if existing.scalar_one_or_none():
        return

    pe = PaymentEvent(
        order_id=order.id,
        stripe_event_id=stripe_event_id,
        event_type="payment_intent.succeeded",
        payload={"id": stripe_event_id, "type": "payment_intent.succeeded"},
    )
    db.add(pe)
    await db.commit()

    campaign = await increment_counter(order.campaign_id, db)
    write_campaign_projection(campaign.id, _campaign_projection_data(campaign))
    await publish_campaign_presale_incremented(campaign.id)

    logger.info(
        "Simulated payment success (DEV_SKIP_STRIPE)",
        extra={"order_id": str(order.id), "campaign_id": str(order.campaign_id)},
    )


async def handle_stripe_webhook(event: dict, db: AsyncSession) -> None:
    """
    Process Stripe webhook event. Idempotency via payment_events.
    Handles: payment_intent.succeeded, payment_intent.payment_failed.
    """
    stripe_event_id = event.get("id")
    if not stripe_event_id:
        return

    existing = await db.execute(
        select(PaymentEvent).where(PaymentEvent.stripe_event_id == stripe_event_id)
    )
    if existing.scalar_one_or_none():
        return

    event_type = event.get("type", "")
    payment_event = PaymentEvent(
        stripe_event_id=stripe_event_id,
        event_type=event_type,
        payload=event,
    )
    db.add(payment_event)
    await db.commit()
    await db.refresh(payment_event)

    order_id = None
    obj = event.get("data", {}).get("object", {})
    pi_id = obj.get("id")

    if pi_id:
        order = await _get_order_by_pi(pi_id, db)
        if order:
            order_id = order.id
            payment_event.order_id = order_id
            await db.commit()

    if event_type == "payment_intent.succeeded":
        await _process_payment_succeeded(order_id, pi_id, db)
    elif event_type == "payment_intent.payment_failed":
        logger.info(
            "Payment failed (webhook)",
            extra={"stripe_event_id": stripe_event_id, "payment_intent_id": pi_id},
        )


async def _get_order_by_pi(pi_id: str, db: AsyncSession) -> Order | None:
    """Look up order by stripe_payment_intent_id."""
    result = await db.execute(
        select(Order).where(Order.stripe_payment_intent_id == pi_id)
    )
    return result.scalar_one_or_none()


async def _process_payment_succeeded(
    order_id: UUID | None, pi_id: str | None, db: AsyncSession
) -> None:
    """Increment campaign counter, write Firestore, publish event."""
    if not order_id or not pi_id:
        return
    order = await get_order(order_id, db)
    if not order or order.status != OrderStatus.PENDING_CAMPAIGN:
        return

    campaign = await increment_counter(order.campaign_id, db)
    write_campaign_projection(campaign.id, _campaign_projection_data(campaign))
    await publish_campaign_presale_incremented(campaign.id)


async def get_order(order_id: UUID, db: AsyncSession) -> Order | None:
    """Get order by id."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalar_one_or_none()


async def get_campaign_orders(campaign_id: UUID, db: AsyncSession) -> list[Order]:
    """Get all orders for a campaign (for batch refund)."""
    result = await db.execute(
        select(Order).where(Order.campaign_id == campaign_id)
    )
    return list(result.scalars().all())


async def batch_refund_campaign(campaign_id: UUID, db: AsyncSession) -> int:
    """
    Refund all non-refunded orders for a campaign. Resumable, idempotent.
    Returns count of orders refunded in this run.
    When DEV_SKIP_STRIPE, marks orders refunded without calling Stripe.
    """
    from platform_api.commerce.stripe_client import issue_refund

    orders = await get_campaign_orders(campaign_id, db)
    refunded = 0
    for order in orders:
        if order.status == OrderStatus.REFUNDED:
            continue

        if settings.dev_skip_stripe:
            order.status = OrderStatus.REFUNDED
            refunded += 1
            logger.info(
                "Simulated refund (DEV_SKIP_STRIPE)",
                extra={"order_id": str(order.id)},
            )
            continue

        try:
            issue_refund(order.stripe_payment_intent_id)
            order.status = OrderStatus.REFUNDED
            refunded += 1
            logger.info(
                "Refund issued",
                extra={"order_id": str(order.id)},
            )
        except Exception as e:
            logger.error(
                "Refund failed",
                extra={"order_id": str(order.id), "error": str(e)},
            )

    if refunded:
        await db.commit()
    return refunded
