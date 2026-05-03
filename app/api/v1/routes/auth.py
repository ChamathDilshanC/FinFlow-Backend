"""
Authenticated user profile routes.

Sign-up and password login are handled by **Supabase Auth** on the frontend; this API
expects ``Authorization: Bearer <Supabase access_token>``.
"""

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import CurrentUserId, get_auth_service
from app.api.v1.schemas.auth import (
    UpdateBudgetRequest,
    UserProfilePatch,
    UserResponse,
)
from app.application.services.auth_service import AuthService
from app.core.exceptions import AppHTTPException
from app.domain.exceptions import DomainError, UserNotFoundError

router = APIRouter()


def _map_domain(exc: DomainError) -> AppHTTPException:
    """Translate predictable domain failures into HTTP errors."""
    if isinstance(exc, UserNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    return AppHTTPException(detail=exc.message, code=exc.code, status_code=400)


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
