"""
Verify Supabase-issued JWT access tokens.

Current Supabase projects often use **asymmetric** signing (e.g. ECC P-256 → ``ES256``)
with keys exposed via JWKS. Older tokens may still use **HS256** with the legacy JWT
secret — optional fallback when :envvar:`SUPABASE_JWT_LEGACY_HS256_SECRET` is set.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

import jwt
from jwt import PyJWKClient

from app.config import Settings


def _issuer(settings: Settings) -> str:
    return settings.supabase_jwt_issuer or f"{settings.supabase_url.rstrip('/')}/auth/v1"


def verify_supabase_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """
    Decode and validate a Supabase user access token.

    Tries ``ES256`` via JWKS first, then optional ``HS256`` with the legacy shared secret.

    Args:
        token: Raw JWT (no ``Bearer`` prefix).
        settings: Application settings including ``supabase_url``.

    Returns:
        JWT payload (claims).

    Raises:
        jwt.PyJWTError: When the token is invalid, expired, or wrongly signed.
    """
    issuer = _issuer(settings)
    audience = settings.supabase_jwt_audience
    base = settings.supabase_url.rstrip("/")
    jwks_url = f"{base}/auth/v1/.well-known/jwks.json"

    try:
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        secret = settings.supabase_jwt_legacy_hs256_secret
        if not secret:
            raise
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "sub"]},
        )


def parse_supabase_user_identity(payload: dict[str, Any]) -> tuple[UUID, str]:
    """
    Extract Supabase user id and email from validated claims.

    Raises:
        ValueError: When ``sub`` or ``email`` is missing/invalid.
    """
    sub_raw = payload.get("sub")
    if not sub_raw:
        msg = "Token missing subject (sub)"
        raise ValueError(msg)
    supabase_sub = UUID(str(sub_raw))

    email = payload.get("email")
    if not email or not str(email).strip():
        msg = "Token missing email claim"
        raise ValueError(msg)

    return supabase_sub, str(email).strip().lower()
