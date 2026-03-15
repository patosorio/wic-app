"""Firestore projection writes. Single location for all Firestore writes."""

import logging
from uuid import UUID

from google.cloud import firestore

from core.config import settings

logger = logging.getLogger(__name__)


def _get_client() -> firestore.Client:
    """Return Firestore client."""
    return firestore.Client(project=settings.gcp_project_id)


def write_campaign_projection(campaign_id: UUID, data: dict) -> None:
    """
    Write campaign projection to Firestore /campaigns/{campaign_id}.
    Fields: status, current_count, target, percentage, days_remaining,
    presale_price, ends_at, release_id.
    Skips if DEV_SKIP_FIRESTORE=true.
    """
    if settings.dev_skip_firestore:
        logger.info(
            "Skipping Firestore write (dev_skip_firestore)",
            extra={"campaign_id": str(campaign_id)},
        )
        return
    client = _get_client()
    doc_ref = client.collection("campaigns").document(str(campaign_id))
    doc_ref.set(data)


def write_release_doc(release_id: UUID, data: dict) -> None:
    """
    Write release document to Firestore /releases/{release_id}.
    Creates or overwrites the document.
    Skips if DEV_SKIP_FIRESTORE=true (local dev without Firestore).
    """
    if settings.dev_skip_firestore:
        logger.info(
            "Skipping Firestore write (dev_skip_firestore)",
            extra={"release_id": str(release_id)},
        )
        return
    client = _get_client()
    doc_ref = client.collection("releases").document(str(release_id))
    doc_ref.set(data)
