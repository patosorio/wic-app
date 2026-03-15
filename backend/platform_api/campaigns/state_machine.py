"""Campaign state machine. Valid transitions only. Every transition logs CampaignEvent."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import InvalidStateTransitionError

from platform_api.campaigns.constants import CAMPAIGN_MINIMUM_TARGET
from platform_api.campaigns.models import Campaign, CampaignEvent, CampaignStatus

# Valid transitions: (from, to)
VALID_TRANSITIONS = {
    (CampaignStatus.DRAFT, CampaignStatus.ACTIVE),
    (CampaignStatus.ACTIVE, CampaignStatus.FUNDED),
    (CampaignStatus.ACTIVE, CampaignStatus.FAILED),
    (CampaignStatus.FAILED, CampaignStatus.REFUNDING),
    (CampaignStatus.REFUNDING, CampaignStatus.CLOSED),
}


def _transition_allowed(from_status: CampaignStatus, to_status: CampaignStatus) -> bool:
    """Return True if transition is valid."""
    return (from_status, to_status) in VALID_TRANSITIONS


async def transition(
    campaign_id: UUID,
    to_status: CampaignStatus,
    triggered_by: str,
    db: AsyncSession,
) -> Campaign:
    """
    Transition campaign to new status. Logs CampaignEvent. Raises InvalidStateTransitionError if illegal.
    """
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise InvalidStateTransitionError("Campaign not found")

    from_status = (
        campaign.status
        if isinstance(campaign.status, CampaignStatus)
        else CampaignStatus(campaign.status)
    )

    if not _transition_allowed(from_status, to_status):
        raise InvalidStateTransitionError(
            f"Invalid transition: {from_status.value} → {to_status.value}"
        )

    event = CampaignEvent(
        campaign_id=campaign_id,
        from_status=from_status.value,
        to_status=to_status.value,
        triggered_by=triggered_by,
    )
    db.add(event)
    campaign.status = to_status
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def transition_to_active(campaign_id: UUID, triggered_by: str, db: AsyncSession) -> Campaign:
    """DRAFT → ACTIVE."""
    return await transition(campaign_id, CampaignStatus.ACTIVE, triggered_by, db)


async def transition_to_funded(campaign_id: UUID, triggered_by: str, db: AsyncSession) -> Campaign:
    """ACTIVE → FUNDED. Call only when current_count >= target."""
    return await transition(campaign_id, CampaignStatus.FUNDED, triggered_by, db)


async def transition_to_failed(campaign_id: UUID, triggered_by: str, db: AsyncSession) -> Campaign:
    """ACTIVE → FAILED. Day-30 job, target not met."""
    return await transition(campaign_id, CampaignStatus.FAILED, triggered_by, db)


async def transition_to_refunding(
    campaign_id: UUID, triggered_by: str, db: AsyncSession
) -> Campaign:
    """FAILED → REFUNDING."""
    return await transition(campaign_id, CampaignStatus.REFUNDING, triggered_by, db)


async def transition_to_closed(campaign_id: UUID, triggered_by: str, db: AsyncSession) -> Campaign:
    """REFUNDING → CLOSED."""
    return await transition(campaign_id, CampaignStatus.CLOSED, triggered_by, db)
