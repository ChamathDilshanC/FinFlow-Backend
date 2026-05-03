"""Expense transaction CRUD."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.dependencies import CurrentUserId, get_transaction_service
from app.api.v1.schemas.transactions import TransactionCreate, TransactionResponse, TransactionUpdate
from app.application.services.transaction_service import TransactionService
from app.core.exceptions import AppHTTPException
from app.domain.exceptions import CategoryNotFoundError, DomainError, TransactionNotFoundError


router = APIRouter()


def _map(exc: DomainError) -> AppHTTPException:
    if isinstance(exc, TransactionNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    if isinstance(exc, CategoryNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    return AppHTTPException(detail=exc.message, code=exc.code, status_code=400)


def _resp(t) -> TransactionResponse:
    return TransactionResponse(
        id=t.id,
        user_id=t.user_id,
        category_id=t.category_id,
        amount=t.amount,
        currency=t.currency,
        occurred_at=t.occurred_at,
        merchant=t.merchant,
        notes=t.notes,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    response: Response,
    user_id: CurrentUserId,
    service: TransactionService = Depends(get_transaction_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category_id: UUID | None = None,
    from_occurred: datetime | None = None,
    to_occurred: datetime | None = None,
) -> list[TransactionResponse]:
    items, total = await service.list_transactions(
        user_id,
        skip=skip,
        limit=limit,
        category_id=category_id,
        from_occurred=from_occurred,
        to_occurred=to_occurred,
    )
    response.headers["X-Total-Count"] = str(total)
    return [_resp(t) for t in items]


@router.post("", response_model=TransactionResponse)
async def create_transaction(
    body: TransactionCreate,
    user_id: CurrentUserId,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    try:
        t = await service.create_transaction(
            user_id,
            category_id=body.category_id,
            amount=body.amount,
            currency=body.currency,
            occurred_at=body.occurred_at,
            merchant=body.merchant,
            notes=body.notes,
        )
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(t)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    user_id: CurrentUserId,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    try:
        t = await service.get_transaction(user_id, transaction_id)
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(t)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    body: TransactionUpdate,
    user_id: CurrentUserId,
    service: TransactionService = Depends(get_transaction_service),
) -> TransactionResponse:
    try:
        t = await service.update_transaction(
            user_id,
            transaction_id,
            category_id=body.category_id,
            amount=body.amount,
            currency=body.currency,
            occurred_at=body.occurred_at,
            merchant=body.merchant,
            notes=body.notes,
        )
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(t)


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: UUID,
    user_id: CurrentUserId,
    service: TransactionService = Depends(get_transaction_service),
) -> dict[str, str]:
    try:
        await service.delete_transaction(user_id, transaction_id)
    except DomainError as exc:
        raise _map(exc) from exc
    return {"detail": "deleted", "code": "DELETED"}
