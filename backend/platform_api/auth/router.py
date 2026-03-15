"""Auth routes: register and me."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.firebase_auth import FirebaseUser, verify_firebase_jwt

from platform_api.auth.models import UserResponse
from platform_api.auth.service import get_or_create_user, get_user_by_firebase_uid

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    user: FirebaseUser = Depends(verify_firebase_jwt),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Create user record in DB after Firebase signup.
    Idempotent: returns existing user if already registered.
    """
    db_user = await get_or_create_user(
        firebase_uid=user.uid,
        email=user.email,
        role=user.role,
        db=db,
    )
    return UserResponse.model_validate(db_user)


@router.get("/me", response_model=UserResponse)
async def me(
    user: FirebaseUser = Depends(verify_firebase_jwt),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Return current user from DB. Registers user if not exists."""
    db_user = await get_user_by_firebase_uid(user.uid, db)
    if not db_user:
        db_user = await get_or_create_user(
            firebase_uid=user.uid,
            email=user.email,
            role=user.role,
            db=db,
        )
    return UserResponse.model_validate(db_user)
