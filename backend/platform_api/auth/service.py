"""Auth service: user lookup and creation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.firebase_auth import UserRole

from platform_api.auth.models import User


async def get_or_create_user(
    firebase_uid: str,
    email: str,
    role: UserRole,
    db: AsyncSession,
) -> User:
    """
    Get existing user by firebase_uid or create one.
    Does not update role on existing users (artist/admin granted by admin).
    """
    existing = await get_user_by_firebase_uid(firebase_uid, db)
    if existing:
        return existing
    user = User(
        firebase_uid=firebase_uid,
        email=email,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user(user_id: UUID, db: AsyncSession) -> User | None:
    """Get user by id."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_firebase_uid(
    firebase_uid: str, db: AsyncSession
) -> User | None:
    """Get user by Firebase UID."""
    result = await db.execute(
        select(User).where(User.firebase_uid == firebase_uid)
    )
    return result.scalar_one_or_none()
