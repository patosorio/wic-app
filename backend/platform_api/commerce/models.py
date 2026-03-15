"""Commerce module models: Order and PaymentEvent."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID

from pydantic import BaseModel, ConfigDict

from core.database import Base


class OrderStatus(str, enum.Enum):
    """Order lifecycle status."""

    PENDING_CAMPAIGN = "pending_campaign"
    IN_PRODUCTION = "in_production"
    REFUNDED = "refunded"
    COMPLETED = "completed"


class Order(Base):
    """Pre-order record."""

    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING_CAMPAIGN
    )
    amount = Column(Numeric(10, 2), nullable=False)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PaymentEvent(Base):
    """Stripe webhook event audit log (idempotency key: stripe_event_id)."""

    __tablename__ = "payment_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    stripe_event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(128), nullable=False)
    payload = Column(JSONB, nullable=False)
    processed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# Pydantic schemas
class OrderCreateRequest(BaseModel):
    """Request body for creating a pre-order."""

    campaign_id: uuid.UUID


class OrderResponse(BaseModel):
    """API response for Order."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    customer_id: uuid.UUID
    status: OrderStatus
    amount: Decimal
    stripe_payment_intent_id: str
    client_secret: str | None = None
    created_at: datetime
