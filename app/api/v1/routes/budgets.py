"""Monthly category budget allocations."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.dependencies import CurrentUserId, get_budget_allocation_service
from app.api.v1.schemas.budgets import BudgetAllocationCreate, BudgetAllocationResponse, BudgetAllocationUpdate
from app.application.services.budget_allocation_service import BudgetAllocationService
from app.core.exceptions import AppHTTPException
from app.domain.exceptions import BudgetNotFoundError, CategoryNotFoundError, DomainError


router = APIRouter()


def _map(exc: DomainError) -> AppHTTPException:
    if isinstance(exc, BudgetNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    if isinstance(exc, CategoryNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    return AppHTTPException(detail=exc.message, code=exc.code, status_code=400)


def _resp(b) -> BudgetAllocationResponse:
    return BudgetAllocationResponse(
        id=b.id,
        user_id=b.user_id,
        category_id=b.category_id,
        budget_month=b.budget_month,
        limit_amount=b.limit_amount,
        currency=b.currency,
        created_at=b.created_at,
        updated_at=b.updated_at,
    )


@router.get("", response_model=list[BudgetAllocationResponse])
async def list_budgets(
    response: Response,
    user_id: CurrentUserId,
    service: BudgetAllocationService = Depends(get_budget_allocation_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[BudgetAllocationResponse]:
    items, total = await service.list_budgets(user_id, skip=skip, limit=limit)
    response.headers["X-Total-Count"] = str(total)
    return [_resp(b) for b in items]


@router.post("", response_model=BudgetAllocationResponse)
async def create_budget(
    body: BudgetAllocationCreate,
    user_id: CurrentUserId,
    service: BudgetAllocationService = Depends(get_budget_allocation_service),
) -> BudgetAllocationResponse:
    try:
        b = await service.create_budget(
            user_id,
            category_id=body.category_id,
            budget_month=body.budget_month,
            limit_amount=body.limit_amount,
            currency=body.currency,
        )
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(b)


@router.get("/{budget_id}", response_model=BudgetAllocationResponse)
async def get_budget(
    budget_id: UUID,
    user_id: CurrentUserId,
    service: BudgetAllocationService = Depends(get_budget_allocation_service),
) -> BudgetAllocationResponse:
    try:
        b = await service.get_budget(user_id, budget_id)
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(b)


@router.put("/{budget_id}", response_model=BudgetAllocationResponse)
async def update_budget(
    budget_id: UUID,
    body: BudgetAllocationUpdate,
    user_id: CurrentUserId,
    service: BudgetAllocationService = Depends(get_budget_allocation_service),
) -> BudgetAllocationResponse:
    try:
        b = await service.update_budget(
            user_id,
            budget_id,
            category_id=body.category_id,
            budget_month=body.budget_month,
            limit_amount=body.limit_amount,
            currency=body.currency,
        )
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(b)


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: UUID,
    user_id: CurrentUserId,
    service: BudgetAllocationService = Depends(get_budget_allocation_service),
) -> dict[str, str]:
    try:
        await service.delete_budget(user_id, budget_id)
    except DomainError as exc:
        raise _map(exc) from exc
    return {"detail": "deleted", "code": "DELETED"}
