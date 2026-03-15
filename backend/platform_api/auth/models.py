"""Auth module models: User and Pydantic schemas."""

import uuid

from sqlalchemy import Column, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base
from core.firebase_auth import UserRole


class User(Base):
    """User record linked to Firebase Auth."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


ROLE_PERMISSIONS = {
    UserRole.CUSTOMER: ["customer"],
    UserRole.ARTIST: ["customer", "artist"],
    UserRole.ADMIN: ["customer", "artist", "admin"],
}


# Pydantic schemas
from datetime import datetime
from uuid import UUID as UUIDType

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """User response for API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUIDType
    firebase_uid: str
    email: str
    role: UserRole
    created_at: datetime
