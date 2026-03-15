"""Campaign service: create, get, list, increment counter."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.firestore import write_campaign_projection

from platform_api.campaigns.constants import (
    CAMPAIGN_DURATION_DAYS,
    CAMPAIGN_MINIMUM_TARGET,
    PRESALE_PRICE_EUR,
    RETAIL_PRICE_EUR,
)
from platform_api.campaigns.models import Campaign, CampaignStatus
from platform_api.campaigns.state_machine import transition_to_active, transition_to_funded


def _campaign_projection_data(campaign: Campaign) -> dict:
    """Build Firestore projection dict for campaign."""
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


async def create_campaign(release_id: UUID, db: AsyncSession) -> Campaign:
    """Create campaign in DRAFT for release. Use launch_campaign to go ACTIVE."""
    campaign = Campaign(
        release_id=release_id,
        status=CampaignStatus.DRAFT,
        target=CAMPAIGN_MINIMUM_TARGET,
        current_count=0,
        presale_price=PRESALE_PRICE_EUR,
        retail_price=RETAIL_PRICE_EUR,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def launch_campaign(campaign_id: UUID, triggered_by: str, db: AsyncSession) -> Campaign:
    """Transition DRAFT → ACTIVE, set starts_at and ends_at."""
    campaign = await get_campaign(campaign_id, db)
    if not campaign:
        raise ValueError("Campaign not found")
    campaign = await transition_to_active(campaign_id, triggered_by, db)
    now = datetime.now(timezone.utc)
    campaign.starts_at = now
    campaign.ends_at = now + timedelta(days=CAMPAIGN_DURATION_DAYS)
    await db.commit()
    await db.refresh(campaign)
    write_campaign_projection(campaign.id, _campaign_projection_data(campaign))
    return campaign


async def get_campaign(campaign_id: UUID, db: AsyncSession) -> Campaign | None:
    """Get campaign by id."""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    return result.scalar_one_or_none()


async def increment_counter(campaign_id: UUID, db: AsyncSession) -> Campaign:
    """
    Increment campaign current_count by 1.
    If current_count >= target, transition ACTIVE → FUNDED.
    Returns updated campaign.
    """
    campaign = await get_campaign(campaign_id, db)
    if not campaign:
        raise ValueError("Campaign not found")
    if campaign.status != CampaignStatus.ACTIVE:
        raise ValueError(f"Campaign must be ACTIVE to increment, got {campaign.status}")
    campaign.current_count += 1
    await db.commit()
    await db.refresh(campaign)

    write_campaign_projection(campaign.id, _campaign_projection_data(campaign))

    if campaign.current_count >= campaign.target:
        campaign = await transition_to_funded(campaign_id, "system", db)
        write_campaign_projection(campaign.id, _campaign_projection_data(campaign))

    return campaign


async def list_active_campaigns(db: AsyncSession) -> list[Campaign]:
    """List campaigns with status ACTIVE."""
    result = await db.execute(
        select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE)
    )
    return list(result.scalars().all())


async def list_almost_funded(db: AsyncSession, min_percentage: float = 70) -> list[Campaign]:
    """List ACTIVE campaigns with percentage >= min_percentage, sorted by closest to target."""
    campaigns = await list_active_campaigns(db)
    almost = [
        c
        for c in campaigns
        if c.target and (c.current_count / c.target * 100) >= min_percentage
    ]
    almost.sort(key=lambda c: c.target - c.current_count)
    return almost


async def list_trending(db: AsyncSession, limit: int = 10) -> list[Campaign]:
    """List ACTIVE campaigns sorted by current_count descending."""
    result = await db.execute(
        select(Campaign)
        .where(Campaign.status == CampaignStatus.ACTIVE)
        .order_by(Campaign.current_count.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
