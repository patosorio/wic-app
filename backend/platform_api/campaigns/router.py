"""Campaign routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.firebase_auth import FirebaseUser, UserRole, require_role

from platform_api.auth.service import get_user_by_firebase_uid
from platform_api.campaigns.models import CampaignResponse
from platform_api.campaigns.service import (
    create_campaign,
    get_campaign,
    launch_campaign,
    list_active_campaigns,
    list_almost_funded,
    list_trending,
)
from platform_api.catalog.service import get_release

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CreateCampaignRequest(BaseModel):
    """Request body for POST /campaigns/."""

    release_id: UUID


@router.post("/", response_model=CampaignResponse)
async def post_campaign(
    body: CreateCampaignRequest,
    db: AsyncSession = Depends(get_db),
    user: FirebaseUser = Depends(require_role(UserRole.ARTIST)),
) -> CampaignResponse:
    """Create and launch campaign for release (artist only)."""
    db_user = await get_user_by_firebase_uid(user.uid, db)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not registered. Call POST /auth/register first.",
        )
    release = await get_release(body.release_id, db)
    if not release:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Release not found",
        )
    if release.artist_id != db_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your release",
        )
    campaign = await create_campaign(body.release_id, db)
    campaign = await launch_campaign(campaign.id, str(db_user.id), db)
    return CampaignResponse.model_validate(campaign)


@router.get("/", response_model=list[CampaignResponse])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
) -> list[CampaignResponse]:
    """List active campaigns."""
    campaigns = await list_active_campaigns(db)
    return [CampaignResponse.model_validate(c) for c in campaigns]


@router.get("/trending/", response_model=list[CampaignResponse])
async def list_trending_campaigns(
    db: AsyncSession = Depends(get_db),
) -> list[CampaignResponse]:
    """List trending (active) campaigns by pre-order count."""
    campaigns = await list_trending(db)
    return [CampaignResponse.model_validate(c) for c in campaigns]


@router.get("/almost-funded/", response_model=list[CampaignResponse])
async def list_almost_funded_campaigns(
    db: AsyncSession = Depends(get_db),
) -> list[CampaignResponse]:
    """List campaigns >= 70% funded, sorted by closest to target."""
    campaigns = await list_almost_funded(db)
    return [CampaignResponse.model_validate(c) for c in campaigns]


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign_route(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    """Get campaign by id."""
    campaign = await get_campaign(campaign_id, db)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return CampaignResponse.model_validate(campaign)
