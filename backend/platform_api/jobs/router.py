"""Internal job endpoints (Cloud Tasks)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.events import publish_campaign_failed

from platform_api.campaigns.models import CampaignStatus
from platform_api.campaigns.service import get_campaign
from platform_api.campaigns.state_machine import (
    transition_to_closed,
    transition_to_failed,
    transition_to_refunding,
)
from platform_api.commerce.service import batch_refund_campaign

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/evaluate-campaign/{campaign_id}")
async def evaluate_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Day-30 Cloud Tasks job. Transitions ACTIVE → FAILED if target not met.
    TODO: Add Cloud Tasks JWT verification (Phase 9).
    """
    campaign = await get_campaign(campaign_id, db)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    if campaign.status != CampaignStatus.ACTIVE:
        return {"status": "skipped", "reason": f"Campaign not ACTIVE ({campaign.status})"}
    if campaign.current_count >= campaign.target:
        return {"status": "skipped", "reason": "Campaign already funded"}
    await transition_to_failed(campaign_id, "system", db)
    await publish_campaign_failed(campaign_id)
    await transition_to_refunding(campaign_id, "system", db)
    refunded = await batch_refund_campaign(campaign_id, db)
    await transition_to_closed(campaign_id, "system", db)
    return {
        "status": "failed",
        "campaign_id": str(campaign_id),
        "orders_refunded": refunded,
    }
