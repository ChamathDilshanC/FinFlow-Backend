"""
Call Supabase GoTrue HTTP endpoints for email/password sign-up and sign-in.

Uses the project's **anon** public API key (same as the Supabase client in browsers).
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import httpx

from app.config import Settings


class SupabaseAuthHttpError(Exception):
    """Non-2xx response from Supabase Auth REST API."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _auth_headers(settings: Settings) -> dict[str, str]:
    key = settings.supabase_anon_key
    if not key:
        msg = "SUPABASE_ANON_KEY is not set"
        raise ValueError(msg)
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _error_message(body: dict[str, Any]) -> str:
    if msg := body.get("msg"):
        return str(msg)
    if desc := body.get("error_description"):
        return str(desc)
    if err := body.get("error"):
        return str(err)
    if code := body.get("error_code"):
        return str(code)
    return "Supabase Auth request failed"


def _parse_user_and_session(data: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """
    Normalize GoTrue JSON: session may be nested under ``session`` or flattened at the root.
    """
    user = data.get("user")
    if not isinstance(user, dict):
        user = {}
    session = data.get("session")
    if isinstance(session, dict) and session.get("access_token"):
        return session, user
    if data.get("access_token"):
        return data, user
    return None, user


def _raise_for_status(status_code: int, body: dict[str, Any]) -> None:
    if status_code < 400:
        return
    raise SupabaseAuthHttpError(status_code, _error_message(body))


async def signup_email_password(
    settings: Settings,
    email: str,
    password: str,
) -> tuple[dict[str, Any] | None, UUID, str, bool]:
    """
    POST ``/auth/v1/signup``.

    Returns:
        Tuple of (session dict or None if no session e.g. email confirmation),
        user id, normalized email, and whether a session was returned.
    """
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/signup"
    payload = {"email": email.strip().lower(), "password": password}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, headers=_auth_headers(settings), json=payload)
    try:
        body = r.json()
    except json.JSONDecodeError:
        r.raise_for_status()
        msg = "Unexpected response from Supabase Auth"
        raise RuntimeError(msg) from None

    if not isinstance(body, dict):
        msg = "Unexpected response from Supabase Auth"
        raise ValueError(msg)

    _raise_for_status(r.status_code, body)

    session, user = _parse_user_and_session(body)
    uid_raw = user.get("id")
    em = user.get("email")
    if not uid_raw or not em:
        msg = "Supabase signup response missing user id or email"
        raise ValueError(msg)
    user_id = UUID(str(uid_raw))
    email_norm = str(em).strip().lower()
    has_session = session is not None and bool(session.get("access_token"))
    return session, user_id, email_norm, has_session


async def signin_email_password(
    settings: Settings,
    email: str,
    password: str,
) -> tuple[dict[str, Any], UUID, str]:
    """POST ``/auth/v1/token?grant_type=password``."""
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/token?grant_type=password"
    payload = {"email": email.strip().lower(), "password": password}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, headers=_auth_headers(settings), json=payload)
    try:
        body = r.json()
    except json.JSONDecodeError:
        r.raise_for_status()
        msg = "Unexpected response from Supabase Auth"
        raise RuntimeError(msg) from None

    if not isinstance(body, dict):
        msg = "Unexpected response from Supabase Auth"
        raise ValueError(msg)

    _raise_for_status(r.status_code, body)

    session, user = _parse_user_and_session(body)
    if session is None or not session.get("access_token"):
        msg = "Supabase login response missing session"
        raise ValueError(msg)
    uid_raw = user.get("id")
    em = user.get("email")
    if not uid_raw or not em:
        msg = "Supabase login response missing user id or email"
        raise ValueError(msg)
    return session, UUID(str(uid_raw)), str(em).strip().lower()
