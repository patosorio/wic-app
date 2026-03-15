"""Pub/Sub event publishing. All publishes go through this module."""

import logging
from uuid import UUID

logger = logging.getLogger(__name__)


async def publish_campaign_presale_incremented(campaign_id: UUID) -> None:
    """
    Publish campaign.presale_incremented event.
    TODO: Wire to Cloud Pub/Sub in Phase 9. Triggers Firestore write, points, notifications.
    """
    logger.info(
        "Campaign presale incremented (event placeholder)",
        extra={"campaign_id": str(campaign_id)},
    )


async def publish_campaign_failed(campaign_id: UUID) -> None:
    """
    Publish campaign.failed event.
    TODO: Wire to Cloud Pub/Sub in Phase 9.
    """
    logger.info(
        "Campaign failed (event placeholder)",
        extra={"campaign_id": str(campaign_id)},
    )
