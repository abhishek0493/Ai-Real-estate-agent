"""Security utilities — API keys, password hashing, and JWT tokens."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt


def get_password_hash(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ── API key generation ────────────────────────────────────────────────


def generate_api_key() -> str:
    """Generate a cryptographically secure, URL-safe API key.

    Uses 32 bytes of entropy (256 bits), resulting in a ~43 character
    URL-safe string.
    """
    return secrets.token_urlsafe(32)


# ── JWT tokens ────────────────────────────────────────────────────────

_ALGORITHM = "HS256"


def create_access_token(
    data: dict[str, Any],
    secret_key: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        data: Claims to encode (must include 'sub' and 'tenant_id').
        secret_key: Secret used to sign the token.
        expires_delta: Token lifetime. Defaults to 60 minutes.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=60))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, secret_key, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret_key: str) -> dict[str, Any]:
    """Decode and verify a JWT access token.

    Raises ``JWTError`` if the token is invalid, expired, or tampered with.
    """
    return jwt.decode(token, secret_key, algorithms=[_ALGORITHM])
