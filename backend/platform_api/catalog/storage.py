"""Cloud Storage helpers for audio and artwork uploads."""

from uuid import UUID

from core.config import settings
from google.cloud import storage


def _get_bucket() -> storage.Bucket:
    """Return the configured GCS bucket."""
    client = storage.Client(project=settings.gcp_project_id)
    return client.bucket(settings.gcs_bucket)


def _blob_path(release_id: UUID, kind: str, name: str) -> str:
    """Build blob path: releases/{release_id}/{kind}/{name}."""
    return f"releases/{release_id}/{kind}/{name}"


def upload_audio(
    file_content: bytes,
    release_id: UUID,
    side: str,
    content_type: str = "audio/wav",
) -> str:
    """
    Upload audio file to Cloud Storage.
    Returns signed URL for private access (1 hour expiry).
    """
    bucket = _get_bucket()
    blob_name = _blob_path(release_id, "audio", f"side_{side}.wav")
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        file_content,
        content_type=content_type,
    )
    url = blob.generate_signed_url(expiration=3600)
    return url


def upload_artwork(
    file_content: bytes,
    release_id: UUID,
    artwork_type: str,
    content_type: str = "image/jpeg",
) -> str:
    """
    Upload artwork to Cloud Storage.
    artwork_type: cover, label_a, label_b.
    Returns signed URL for private access (1 hour expiry).
    """
    bucket = _get_bucket()
    ext = "jpg" if "jpeg" in content_type else "png"
    blob_name = _blob_path(release_id, "artwork", f"{artwork_type}.{ext}")
    blob = bucket.blob(blob_name)
    blob.upload_from_string(
        file_content,
        content_type=content_type,
    )
    url = blob.generate_signed_url(expiration=3600)
    return url
