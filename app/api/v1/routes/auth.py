"""
Authentication endpoints: register, login, profile, and budget updates.
"""

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import CurrentUserId, get_auth_service
from app.api.v1.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateBudgetRequest,
    UserProfilePatch,
    UserResponse,
)
from app.application.services.auth_service import AuthService
from app.core.exceptions import AppHTTPException
from app.domain.exceptions import (
    DomainError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UserNotFoundError,
)

router = APIRouter()


def _map_domain(exc: DomainError) -> AppHTTPException:
    """Translate predictable domain failures into HTTP errors."""
    if isinstance(exc, EmailAlreadyRegisteredError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=409)
    if isinstance(exc, InvalidCredentialsError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=401)
    if isinstance(exc, UserNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    return AppHTTPException(detail=exc.message, code=exc.code, status_code=400)


@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Register a new account and return an access token."""
    try:
        tokens = await auth_service.register(body.email, body.password)
    except DomainError as exc:
        raise _map_domain(exc) from exc
    return TokenResponse(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate and receive an access token."""
    try:
        tokens = await auth_service.login(body.email, body.password)
    except DomainError as exc:
        raise _map_domain(exc) from exc
    return TokenResponse(
        access_token=tokens.access_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
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
