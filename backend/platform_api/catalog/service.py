"""Catalog service: release creation and queries."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.firestore import write_release_doc

from platform_api.catalog.models import (
    CreateReleaseRequest,
    Release,
    ReleaseDoc,
    ReleaseFormat,
    ReleaseStatus,
)


async def create_release(
    data: CreateReleaseRequest,
    artist_id: UUID,
    db: AsyncSession,
) -> Release:
    """
    Create release in Postgres and write Firestore doc.
    """
    release = Release(
        artist_id=artist_id,
        firestore_doc_id=None,
        status=ReleaseStatus.DRAFT,
        format=data.format,
    )
    db.add(release)
    await db.flush()

    firestore_doc_id = str(release.id)
    release.firestore_doc_id = firestore_doc_id

    doc_data = ReleaseDoc(
        title=data.title,
        artist_name=data.artist_name,
        catalog_number=data.catalog_number,
        format=data.format.value,
        audio_urls=data.audio_urls,
        artwork_urls=data.artwork_urls,
        label_color=data.label_color,
        tracklist=data.tracklist,
        description=data.description,
        tags=data.tags,
    ).model_dump(mode="json")

    write_release_doc(release.id, doc_data)

    await db.commit()
    await db.refresh(release)
    return release


async def get_release(release_id: UUID, db: AsyncSession) -> Release | None:
    """Get release by id."""
    result = await db.execute(select(Release).where(Release.id == release_id))
    return result.scalar_one_or_none()


async def list_releases(
    db: AsyncSession,
    artist_id: UUID | None = None,
    status: ReleaseStatus | None = None,
) -> list[Release]:
    """List releases with optional filters."""
    stmt = select(Release)
    if artist_id is not None:
        stmt = stmt.where(Release.artist_id == artist_id)
    if status is not None:
        stmt = stmt.where(Release.status == status)
    stmt = stmt.order_by(Release.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())
