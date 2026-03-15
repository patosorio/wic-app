"""Catalog routes: releases."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.firebase_auth import FirebaseUser, UserRole, require_role

from platform_api.auth.service import get_user_by_firebase_uid
from platform_api.catalog.models import (
    CreateReleaseRequest,
    ReleaseResponse,
    ReleaseStatus,
)
from platform_api.catalog.service import create_release, get_release, list_releases

router = APIRouter(prefix="/releases", tags=["releases"])


@router.post("/", response_model=ReleaseResponse)
async def post_release(
    body: CreateReleaseRequest,
    db: AsyncSession = Depends(get_db),
    user: FirebaseUser = Depends(require_role(UserRole.ARTIST)),
) -> ReleaseResponse:
    """Create release (artist only)."""
    db_user = await get_user_by_firebase_uid(user.uid, db)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not registered. Call POST /auth/register first.",
        )
    release = await create_release(
        data=body,
        artist_id=db_user.id,
        db=db,
    )
    return ReleaseResponse.model_validate(release)


@router.get("/", response_model=list[ReleaseResponse])
async def list_releases_route(
    db: AsyncSession = Depends(get_db),
    artist_id: UUID | None = Query(None),
    status_filter: ReleaseStatus | None = Query(None, alias="status"),
) -> list[ReleaseResponse]:
    """List releases with optional filters."""
    releases = await list_releases(
        db=db,
        artist_id=artist_id,
        status=status_filter,
    )
    return [ReleaseResponse.model_validate(r) for r in releases]


@router.get("/{release_id}", response_model=ReleaseResponse)
async def get_release_route(
    release_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ReleaseResponse:
    """Get release by id."""
    release = await get_release(release_id, db)
    if not release:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Release not found",
        )
    return ReleaseResponse.model_validate(release)
