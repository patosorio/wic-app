"""Catalog module: Release (Postgres) and ReleaseDoc (Firestore schema)."""

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class ReleaseStatus(str, enum.Enum):
    """Release lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ReleaseFormat(str, enum.Enum):
    """Vinyl format."""

    TEN_INCH = "10in"
    TWELVE_INCH = "12in"
    DOUBLE_TWELVE = "2x12in"


class Release(Base):
    """Release record in Postgres. Links to Firestore doc for metadata."""

    __tablename__ = "releases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artist_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    firestore_doc_id = Column(String(128), unique=True, nullable=True, index=True)
    status = Column(
        Enum(ReleaseStatus), nullable=False, default=ReleaseStatus.DRAFT
    )
    format = Column(Enum(ReleaseFormat), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# --- Firestore ReleaseDoc schema (not a DB table) ---


class TrackItem(BaseModel):
    """Track item for tracklist."""

    side: str  # "A" | "B"
    position: int
    title: str
    duration_seconds: int


class AudioUrls(BaseModel):
    """Audio file URLs."""

    side_a: str = ""
    side_b: str = ""


class ArtworkUrls(BaseModel):
    """Artwork file URLs."""

    cover: str = ""
    label_a: str = ""
    label_b: str = ""


class ReleaseDoc(BaseModel):
    """Firestore document shape for /releases/{id}. Not a DB table."""

    model_config = ConfigDict(extra="forbid")

    title: str
    artist_name: str
    catalog_number: str
    format: str  # "10in" | "12in" | "2x12in"
    audio_urls: AudioUrls
    artwork_urls: ArtworkUrls
    label_color: str  # "black" | "white" | "custom"
    tracklist: list[TrackItem]
    description: str
    tags: list[str]


# --- API schemas ---


class CreateReleaseRequest(BaseModel):
    """Request body for POST /releases/."""

    title: str
    artist_name: str
    catalog_number: str
    format: ReleaseFormat
    audio_urls: AudioUrls
    artwork_urls: ArtworkUrls
    label_color: str = "black"
    tracklist: list[TrackItem] = []
    description: str = ""
    tags: list[str] = []


class ReleaseResponse(BaseModel):
    """API response for Release."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    artist_id: uuid.UUID
    firestore_doc_id: str | None
    status: ReleaseStatus
    format: ReleaseFormat
    created_at: datetime
