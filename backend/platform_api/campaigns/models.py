"""Campaign module models."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID

from pydantic import BaseModel, ConfigDict

from core.database import Base


class CampaignStatus(str, enum.Enum):
    """Campaign lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    FUNDED = "funded"
    FAILED = "failed"
    REFUNDING = "refunding"
    CLOSED = "closed"


class Campaign(Base):
    """Campaign record."""

    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    release_id = Column(
        UUID(as_uuid=True),
        ForeignKey("releases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
    )
    status = Column(
        Enum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT
    )
    target = Column(Integer, nullable=False, default=30)
    current_count = Column(Integer, nullable=False, default=0)
    presale_price = Column(Numeric(10, 2), nullable=False)
    retail_price = Column(Numeric(10, 2), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CampaignEvent(Base):
    """Campaign state transition audit log."""

    __tablename__ = "campaign_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status = Column(String(64), nullable=False)
    to_status = Column(String(64), nullable=False)
    triggered_by = Column(String(128), nullable=False)  # system | user_id
    occurred_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# Pydantic schemas
class CampaignResponse(BaseModel):
    """API response for Campaign."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    release_id: uuid.UUID
    status: CampaignStatus
    target: int
    current_count: int
    presale_price: Decimal
    retail_price: Decimal
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime
