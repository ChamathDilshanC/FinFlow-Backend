"""
Auth routes: email/password register and login via **Supabase Auth** REST, profile under JWT.

Protected handlers expect ``Authorization: Bearer <Supabase access_token>``.
"""

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.api.v1.dependencies import CurrentUserId, get_auth_service
from app.api.v1.schemas.auth import (
    AuthSessionResponse,
    EmailPasswordRequest,
    UpdateBudgetRequest,
    UserProfilePatch,
    UserResponse,
)
from app.application.services.auth_service import AuthService
from app.config import Settings, get_settings
from app.core.exceptions import AppHTTPException
from app.core.supabase_auth_http import (
    SupabaseAuthHttpError,
    signin_email_password,
    signup_email_password,
)
from app.domain.exceptions import DomainError, IdentityEmailConflictError, UserNotFoundError

router = APIRouter()

_ALLOWED_OAUTH_BRIDGE_SCHEMES = frozenset({"exp", "finflow"})


@router.get("/oauth-bridge")
async def oauth_bridge(request: Request) -> RedirectResponse:
    """
    Supabase redirects here with ``code`` / ``state`` (HTTPS), then we 302 to the app deep link.

    iOS ``ASWebAuthenticationSession`` sometimes mis-handles a direct ``exp://`` redirect from
    Supabase; an intermediate stable HTTPS URL avoids Safari showing ``localhost`` (Site URL)
    or a broken final hop.
    """
    pairs = list(request.query_params.multi_items())
    next_url: str | None = None
    oauth_pairs: list[tuple[str, str]] = []
    for key, value in pairs:
        if key == "next" and next_url is None:
            next_url = value
        elif key != "next":
            oauth_pairs.append((key, value))

    if not next_url:
        raise HTTPException(status_code=400, detail="Missing next query parameter")

    dest = urlparse(next_url)
    if dest.scheme not in _ALLOWED_OAUTH_BRIDGE_SCHEMES:
        raise HTTPException(
            status_code=400,
            detail="next must be exp:// (Expo Go) or finflow:// (dev build)",
        )

    merged_query = urlencode(parse_qsl(dest.query, keep_blank_values=True) + oauth_pairs)
    location = urlunparse(
        (dest.scheme, dest.netloc, dest.path, dest.params, merged_query, dest.fragment),
    )
    return RedirectResponse(url=location, status_code=302)


def _map_domain(exc: DomainError) -> AppHTTPException:
    """Translate predictable domain failures into HTTP errors."""
    if isinstance(exc, UserNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    return AppHTTPException(detail=exc.message, code=exc.code, status_code=400)


def _http_status_for_supabase(exc: SupabaseAuthHttpError) -> int:
    if 400 <= exc.status_code < 500:
        return exc.status_code
    return 502


def _session_to_response_fields(session: dict[str, Any] | None) -> dict[str, Any]:
    if not session:
        return {
            "access_token": None,
            "refresh_token": None,
            "expires_in": None,
            "token_type": "bearer",
        }
    return {
        "access_token": session.get("access_token"),
        "refresh_token": session.get("refresh_token"),
        "expires_in": session.get("expires_in"),
        "token_type": str(session.get("token_type") or "bearer"),
    }


@router.post("/register", response_model=AuthSessionResponse)
async def register_email_password(
    body: EmailPasswordRequest,
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthSessionResponse:
    """
    Register with email and password through Supabase Auth (Email provider must be enabled).

    Syncs a local ``users`` row. If project **Confirm email** is on, tokens may be omitted until verification.
    """
    if not settings.supabase_anon_key:
        raise AppHTTPException(
            detail="Email/password auth is not configured (set SUPABASE_ANON_KEY)",
            code="AUTH_NOT_CONFIGURED",
            status_code=503,
        )
    try:
        session, uid, email_norm, has_session = await signup_email_password(
            settings, body.email, body.password
        )
        await auth_service.sync_supabase_user(uid, email_norm)
    except SupabaseAuthHttpError as exc:
        raise AppHTTPException(
            detail=exc.message,
            code="SUPABASE_AUTH_ERROR",
            status_code=_http_status_for_supabase(exc),
        ) from exc
    except IdentityEmailConflictError as exc:
        raise AppHTTPException(
            detail=exc.message,
            code=exc.code,
            status_code=409,
        ) from exc
    except ValueError as exc:
        raise AppHTTPException(
            detail=str(exc),
            code="BAD_AUTH_RESPONSE",
            status_code=502,
        ) from exc

    fields = _session_to_response_fields(session)
    return AuthSessionResponse(
        **fields,
        requires_email_confirmation=not has_session,
        user_id=uid,
        email=email_norm,
    )


@router.post("/login", response_model=AuthSessionResponse)
async def login_email_password(
    body: EmailPasswordRequest,
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthSessionResponse:
    """Sign in with email and password; returns Supabase session tokens for ``Authorization: Bearer``."""
    if not settings.supabase_anon_key:
        raise AppHTTPException(
            detail="Email/password auth is not configured (set SUPABASE_ANON_KEY)",
            code="AUTH_NOT_CONFIGURED",
            status_code=503,
        )
    try:
        session, uid, email_norm = await signin_email_password(
            settings, body.email, body.password
        )
        await auth_service.sync_supabase_user(uid, email_norm)
    except SupabaseAuthHttpError:
        raise AppHTTPException(
            detail="Invalid email or password",
            code="INVALID_CREDENTIALS",
            status_code=401,
        ) from None
    except IdentityEmailConflictError as exc:
        raise AppHTTPException(
            detail=exc.message,
            code=exc.code,
            status_code=409,
        ) from exc
    except ValueError as exc:
        raise AppHTTPException(
            detail=str(exc),
            code="BAD_AUTH_RESPONSE",
            status_code=502,
        ) from exc

    fields = _session_to_response_fields(session)
    return AuthSessionResponse(
        **fields,
        requires_email_confirmation=False,
        user_id=uid,
        email=email_norm,
    )


@router.get("/me", response_model=UserResponse)
async def read_me(
    user_id: CurrentUserId,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Return the authenticated user's profile."""
    try:
        user = await auth_service.get_user(user_id)
    except DomainError as exc:
        raise _map_domain(exc) from exc
    return UserResponse(
        id=user.id,
        email=user.email,
        monthly_budget=user.monthly_budget,
        default_currency=user.default_currency,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch("/me", response_model=UserResponse)
async def patch_me(
    body: UserProfilePatch,
    user_id: CurrentUserId,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Partially update profile (budget and/or default currency)."""
    try:
        user = await auth_service.patch_profile(user_id, body.model_dump(exclude_unset=True))
    except DomainError as exc:
        raise _map_domain(exc) from exc
    return UserResponse(
        id=user.id,
        email=user.email,
        monthly_budget=user.monthly_budget,
        default_currency=user.default_currency,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.patch("/me/budget", response_model=UserResponse)
async def update_budget(
    body: UpdateBudgetRequest,
    user_id: CurrentUserId,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Update the authenticated user's monthly budget cap."""
    try:
        user = await auth_service.update_monthly_budget(user_id, body.monthly_budget)
    except DomainError as exc:
        raise _map_domain(exc) from exc
    return UserResponse(
        id=user.id,
        email=user.email,
        monthly_budget=user.monthly_budget,
        default_currency=user.default_currency,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
