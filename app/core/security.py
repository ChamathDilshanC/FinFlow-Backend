"""
Authentication primitives: bcrypt password hashing and JWT access tokens.

Password hashing uses the ``bcrypt`` library directly (not passlib) for compatibility
with bcrypt 4.x/5.x; passlib's bcrypt backend trips compatibility checks on newer bcrypt.

The token payload reserves fields so refresh tokens can be added later without
breaking existing clients (e.g. ``token_type`` distinguishes access vs refresh).
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import Settings


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Bcrypt accepts at most 72 **bytes** (UTF-8). Callers should validate length.

    Args:
        plain_password: User-supplied password.

    Returns:
        ASCII bcrypt hash string for persistence.

    Raises:
        ValueError: When the password exceeds bcrypt's 72-byte limit.
    """
    pwd_bytes = plain_password.encode("utf-8")
    if len(pwd_bytes) > 72:
        msg = "Password exceeds bcrypt limit of 72 bytes"
        raise ValueError(msg)
    hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode("ascii")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: Candidate password.
        password_hash: Stored bcrypt hash.

    Returns:
        ``True`` when the password matches.
    """
    pwd_bytes = plain_password.encode("utf-8")
    if len(pwd_bytes) > 72:
        return False
    try:
        return bcrypt.checkpw(pwd_bytes, password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    *,
    subject_user_id: UUID,
    settings: Settings,
    expires_delta: timedelta | None = None,
    token_type: str = "access",
) -> str:
    """
    Mint a signed JWT access token.

    Args:
        subject_user_id: ``sub`` claim (user id).
        settings: JWT signing configuration.
        expires_delta: Optional override TTL; defaults to ``access_token_expire_minutes``.
        token_type: ``access`` for MVP; reserve ``refresh`` for future rotation.

    Returns:
        Serialized JWT string (Bearer token).
    """
    expire = datetime.now(tz=UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": str(subject_user_id),
        "exp": expire,
        "iat": datetime.now(tz=UTC),
        "token_type": token_type,
        # Reserved for future refresh-token sessions / rotation metadata:
        "ver": 1,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """
    Decode and validate a JWT using configured algorithms and secret.

    Args:
        token: Bearer token without ``Bearer `` prefix.
        settings: JWT verification configuration.

    Returns:
        Decoded claims dictionary.

    Raises:
        JWTError: When signature, expiry, or format validation fails.
    """
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def parse_user_id_from_payload(payload: dict[str, Any]) -> UUID:
    """
    Extract the authenticated user's id from validated JWT claims.

    Args:
        payload: Output of :func:`decode_access_token`.

    Returns:
        User UUID from ``sub``.

    Raises:
        ValueError: When ``sub`` is missing or not a valid UUID.
    """
    sub = payload.get("sub")
    if not sub:
        msg = "Token missing subject"
        raise ValueError(msg)
    return UUID(str(sub))
