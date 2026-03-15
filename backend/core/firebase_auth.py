"""Firebase JWT verification and role enforcement."""

from enum import Enum
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import settings

security = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    """User roles. Default on signup: customer."""

    CUSTOMER = "customer"
    ARTIST = "artist"
    ADMIN = "admin"


ROLE_HIERARCHY = {
    UserRole.CUSTOMER: [UserRole.CUSTOMER],
    UserRole.ARTIST: [UserRole.CUSTOMER, UserRole.ARTIST],
    UserRole.ADMIN: [UserRole.CUSTOMER, UserRole.ARTIST, UserRole.ADMIN],
}


class FirebaseUser:
    """Authenticated user from Firebase JWT or dev bypass."""

    def __init__(self, uid: str, email: str, role: UserRole) -> None:
        self.uid = uid
        self.email = email
        self.role = role


def _get_dev_user() -> FirebaseUser:
    """Return a mock user for local development when bypass is enabled."""
    return FirebaseUser(
        uid="dev-uid-local",
        email="dev@local.test",
        role=UserRole.ADMIN,
    )


async def verify_firebase_jwt(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> FirebaseUser:
    """
    Verify Firebase JWT from Authorization: Bearer <token>.
    Returns FirebaseUser. Raises 401 if invalid or missing.
    Dev bypass: when DEV_BYPASS_AUTH=true, accepts 'Bearer dev' for local testing.
    """
    if settings.dev_bypass_auth:
        if credentials and credentials.credentials == "dev":
            return _get_dev_user()
        # Without valid dev token, still require something in bypass mode
        if not credentials or credentials.credentials != "dev":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Dev bypass: use Authorization: Bearer dev",
            )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    try:
        import firebase_admin
        from firebase_admin import auth, credentials

        if not firebase_admin._apps:
            key_path = settings.firebase_service_account_key_path
            if key_path:
                path = Path(key_path)
                if not path.is_absolute():
                    backend_root = Path(__file__).resolve().parent.parent
                    path = backend_root / key_path
                cred = credentials.Certificate(str(path))
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()

        decoded = auth.verify_id_token(credentials.credentials)
        uid = decoded["uid"]
        email = decoded.get("email", "") or ""
        # Role from custom claim or default to customer
        role_str = decoded.get("role", "customer")
        try:
            role = UserRole(role_str)
        except ValueError:
            role = UserRole.CUSTOMER
        return FirebaseUser(uid=uid, email=email, role=role)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e


def require_role(required_role: UserRole):
    """
    Dependency factory: requires user to have at least the given role.
    Must be used after verify_firebase_jwt.
    """

    async def _require_role(
        user: Annotated[FirebaseUser, Depends(verify_firebase_jwt)],
    ) -> FirebaseUser:
        allowed = ROLE_HIERARCHY.get(user.role, [])
        if required_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires {required_role.value}",
            )
        return user

    return _require_role
