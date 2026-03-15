"""Unit tests for campaign state machine."""

import uuid

import pytest
from sqlalchemy import select

# Import models to register with Base.metadata
from platform_api.auth.models import User  # noqa: F401
from platform_api.catalog.models import Release  # noqa: F401
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from core.exceptions import InvalidStateTransitionError
from platform_api.campaigns.models import Campaign, CampaignEvent, CampaignStatus
from platform_api.campaigns.state_machine import (
    transition_to_active,
    transition_to_closed,
    transition_to_failed,
    transition_to_funded,
    transition_to_refunding,
)


@pytest.fixture
async def db_session():
    """Create in-memory SQLite session for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def draft_campaign(db_session: AsyncSession) -> Campaign:
    """Create a campaign in DRAFT."""
    campaign = Campaign(
        id=uuid.uuid4(),
        release_id=uuid.uuid4(),
        status=CampaignStatus.DRAFT,
        target=30,
        current_count=0,
        presale_price=19.99,
        retail_price=25.99,
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    return campaign


@pytest.fixture
async def active_campaign(db_session: AsyncSession) -> Campaign:
    """Create a campaign in ACTIVE."""
    campaign = Campaign(
        id=uuid.uuid4(),
        release_id=uuid.uuid4(),
        status=CampaignStatus.ACTIVE,
        target=30,
        current_count=10,
        presale_price=19.99,
        retail_price=25.99,
    )
    db_session.add(campaign)
    await db_session.commit()
    await db_session.refresh(campaign)
    return campaign


@pytest.mark.asyncio
async def test_draft_to_active(draft_campaign: Campaign, db_session: AsyncSession):
    """DRAFT → ACTIVE is valid."""
    result = await transition_to_active(
        draft_campaign.id, "user-123", db_session
    )
    assert result.status == CampaignStatus.ACTIVE
    events = await db_session.execute(
        select(CampaignEvent).where(CampaignEvent.campaign_id == draft_campaign.id)
    )
    event = events.scalar_one()
    assert event.from_status == "draft"
    assert event.to_status == "active"


@pytest.mark.asyncio
async def test_active_to_funded(active_campaign: Campaign, db_session: AsyncSession):
    """ACTIVE → FUNDED is valid."""
    result = await transition_to_funded(
        active_campaign.id, "system", db_session
    )
    assert result.status == CampaignStatus.FUNDED


@pytest.mark.asyncio
async def test_active_to_failed(active_campaign: Campaign, db_session: AsyncSession):
    """ACTIVE → FAILED is valid."""
    result = await transition_to_failed(
        active_campaign.id, "system", db_session
    )
    assert result.status == CampaignStatus.FAILED


@pytest.mark.asyncio
async def test_invalid_draft_to_funded(draft_campaign: Campaign, db_session: AsyncSession):
    """DRAFT → FUNDED is invalid."""
    with pytest.raises(InvalidStateTransitionError):
        await transition_to_funded(draft_campaign.id, "system", db_session)


@pytest.mark.asyncio
async def test_invalid_active_from_draft(draft_campaign: Campaign, db_session: AsyncSession):
    """Cannot transition to ACTIVE twice (campaign already ACTIVE)."""
    await transition_to_active(draft_campaign.id, "user", db_session)
    with pytest.raises(InvalidStateTransitionError):
        await transition_to_active(draft_campaign.id, "user", db_session)
