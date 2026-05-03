"""
Subscription CRUD with pagination (``skip`` / ``limit``).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.dependencies import CurrentUserId, get_subscription_service
from app.api.v1.schemas.subscription import (
    BillingCycleSchema,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
)
from app.application.finance import monthly_equivalent
from app.application.services.subscription_service import SubscriptionService
from app.core.exceptions import AppHTTPException
from app.domain.entities.subscription import BillingCycle, Subscription
from app.domain.exceptions import DomainError, SubscriptionNotFoundError

router = APIRouter()


def _map_domain(exc: DomainError) -> AppHTTPException:
    """Map subscription domain errors to HTTP responses."""
    if isinstance(exc, SubscriptionNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    return AppHTTPException(detail=exc.message, code=exc.code, status_code=400)


def _to_cycle(schema: BillingCycleSchema) -> BillingCycle:
    """Convert API enum to domain enum."""
    return BillingCycle(schema.value)


def _to_response(entity: Subscription) -> SubscriptionResponse:
    """Map domain entity to API model including derived monthly equivalent."""
    me = monthly_equivalent(entity.amount, entity.billing_cycle)
    return SubscriptionResponse(
        id=entity.id,
        user_id=entity.user_id,
        name=entity.name,
        amount=entity.amount,
        currency=entity.currency,
        billing_cycle=BillingCycleSchema(entity.billing_cycle.value),
        category=entity.category,
        monthly_limit=entity.monthly_limit,
        start_date=entity.start_date,
        next_renewal_date=entity.next_renewal_date,
        is_active=entity.is_active,
        notes=entity.notes,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        monthly_equivalent=me,
    )


@router.get("", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    response: Response,
    user_id: CurrentUserId,
    service: SubscriptionService = Depends(get_subscription_service),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    active_only: bool | None = Query(default=None),
) -> list[SubscriptionResponse]:
    """List subscriptions with pagination (total count in ``X-Total-Count`` header)."""
    page = await service.list_subscriptions(user_id, skip=skip, limit=limit, active_only=active_only)
    response.headers["X-Total-Count"] = str(page.total)
    return [_to_response(s) for s in page.items]


@router.post("", response_model=SubscriptionResponse)
async def create_subscription(
    body: SubscriptionCreate,
    user_id: CurrentUserId,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    """Create a subscription for the authenticated user."""
    try:
        created = await service.create_subscription(
            user_id,
            name=body.name,
            amount=body.amount,
            currency=body.currency,
            billing_cycle=_to_cycle(body.billing_cycle),
            category=body.category,
            monthly_limit=body.monthly_limit,
            start_date=body.start_date,
            next_renewal_date=body.next_renewal_date,
            is_active=body.is_active,
            notes=body.notes,
        )
    except ValueError as exc:
        raise AppHTTPException(detail=str(exc), code="INVALID_SUBSCRIPTION", status_code=400) from exc
    return _to_response(created)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: UUID,
    user_id: CurrentUserId,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    """Fetch one subscription by id."""
    try:
        sub = await service.get_subscription(user_id, subscription_id)
    except DomainError as exc:
        raise _map_domain(exc) from exc
    return _to_response(sub)


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: UUID,
    body: SubscriptionUpdate,
    user_id: CurrentUserId,
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    """Update a subscription (full replacement semantics)."""
    try:
        updated = await service.update_subscription(
            user_id,
            subscription_id,
            name=body.name,
            amount=body.amount,
            currency=body.currency,
            billing_cycle=_to_cycle(body.billing_cycle),
            category=body.category,
            monthly_limit=body.monthly_limit,
            start_date=body.start_date,
            next_renewal_date=body.next_renewal_date,
            is_active=body.is_active,
            notes=body.notes,
        )
    except DomainError as exc:
        raise _map_domain(exc) from exc
    except ValueError as exc:
        raise AppHTTPException(detail=str(exc), code="INVALID_SUBSCRIPTION", status_code=400) from exc
    return _to_response(updated)


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: UUID,
    user_id: CurrentUserId,
    service: SubscriptionService = Depends(get_subscription_service),
) -> dict[str, str]:
    """Delete a subscription."""
    try:
        await service.delete_subscription(user_id, subscription_id)
    except DomainError as exc:
        raise _map_domain(exc) from exc
    return {"detail": "deleted", "code": "DELETED"}
