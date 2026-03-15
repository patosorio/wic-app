"""add orders and payment_events tables

Revision ID: a1b2c3d4e5f6
Revises: 9f258f117a81
Create Date: 2026-03-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "9f258f117a81"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("campaign_id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING_CAMPAIGN",
                "IN_PRODUCTION",
                "REFUNDED",
                "COMPLETED",
                name="orderstatus",
            ),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_orders_campaign_id"), "orders", ["campaign_id"], unique=False
    )
    op.create_index(
        op.f("ix_orders_customer_id"), "orders", ["customer_id"], unique=False
    )
    op.create_index(
        op.f("ix_orders_stripe_payment_intent_id"),
        "orders",
        ["stripe_payment_intent_id"],
        unique=True,
    )

    op.create_table(
        "payment_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("order_id", sa.UUID(), nullable=True),
        sa.Column("stripe_event_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload", JSONB(), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_payment_events_order_id"),
        "payment_events",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_events_stripe_event_id"),
        "payment_events",
        ["stripe_event_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_payment_events_stripe_event_id"),
        table_name="payment_events",
    )
    op.drop_index(op.f("ix_payment_events_order_id"), table_name="payment_events")
    op.drop_table("payment_events")
    op.drop_index(
        op.f("ix_orders_stripe_payment_intent_id"), table_name="orders"
    )
    op.drop_index(op.f("ix_orders_customer_id"), table_name="orders")
    op.drop_index(op.f("ix_orders_campaign_id"), table_name="orders")
    op.drop_table("orders")
    op.execute("DROP TYPE IF EXISTS orderstatus")
