"""Password hashing and JWT handling."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings


def hash_secret(secret: str) -> str:
    """Return bcrypt hash of a plain text secret."""
    return bcrypt.hashpw(secret.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_secret(secret: str, secret_hashed: str) -> bool:
    """Verify a plain text secret against a bcrypt hash."""
    return bcrypt.checkpw(secret.encode("utf-8"), secret_hashed.encode("utf-8"))


def create_access_token(
    user_id: int, user_name: str, expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT for the user."""
    settings = get_settings()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(hours=settings.jwt_expire_hours))
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "username": user_name,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> dict:
    """Decode and verify JWT. Raises jwt.InvalidTokenError subclasses."""
    settings = get_settings()
    return jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
