"""Payment log CRUD."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.dependencies import CurrentUserId, get_payment_record_service
from app.api.v1.schemas.payments import (
    PaymentCreate,
    PaymentResponse,
    PaymentSourceSchema,
    PaymentStatusSchema,
    PaymentUpdate,
)
from app.application.services.payment_record_service import PaymentRecordService
from app.core.exceptions import AppHTTPException
from app.domain.entities.payment import PaymentSource, PaymentStatus
from app.domain.exceptions import DomainError, PaymentNotFoundError, SubscriptionNotFoundError


router = APIRouter()


def _map(exc: DomainError) -> AppHTTPException:
    if isinstance(exc, PaymentNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    if isinstance(exc, SubscriptionNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    return AppHTTPException(detail=exc.message, code=exc.code, status_code=400)


def _status(s: PaymentStatusSchema) -> PaymentStatus:
    return PaymentStatus(s.value)


def _source(s: PaymentSourceSchema) -> PaymentSource:
    return PaymentSource(s.value)


def _resp(p) -> PaymentResponse:
    return PaymentResponse(
        id=p.id,
        user_id=p.user_id,
        subscription_id=p.subscription_id,
        amount=p.amount,
        currency=p.currency,
        paid_at=p.paid_at,
        period_start=p.period_start,
        period_end=p.period_end,
        status=PaymentStatusSchema(p.status.value),
        source=PaymentSourceSchema(p.source.value),
        notes=p.notes,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=list[PaymentResponse])
async def list_payments(
    response: Response,
    user_id: CurrentUserId,
    service: PaymentRecordService = Depends(get_payment_record_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    subscription_id: UUID | None = None,
) -> list[PaymentResponse]:
    items, total = await service.list_payments(
        user_id,
        skip=skip,
        limit=limit,
        subscription_id=subscription_id,
    )
    response.headers["X-Total-Count"] = str(total)
    return [_resp(p) for p in items]


@router.post("", response_model=PaymentResponse)
async def create_payment(
    body: PaymentCreate,
    user_id: CurrentUserId,
    service: PaymentRecordService = Depends(get_payment_record_service),
) -> PaymentResponse:
    try:
        p = await service.create_payment(
            user_id,
            subscription_id=body.subscription_id,
            amount=body.amount,
            currency=body.currency,
            paid_at=body.paid_at,
            period_start=body.period_start,
            period_end=body.period_end,
            status=_status(body.status),
            source=_source(body.source),
            notes=body.notes,
        )
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(p)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    user_id: CurrentUserId,
    service: PaymentRecordService = Depends(get_payment_record_service),
) -> PaymentResponse:
    try:
        p = await service.get_payment(user_id, payment_id)
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(p)


@router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: UUID,
    body: PaymentUpdate,
    user_id: CurrentUserId,
    service: PaymentRecordService = Depends(get_payment_record_service),
) -> PaymentResponse:
    try:
        p = await service.update_payment(
            user_id,
            payment_id,
            subscription_id=body.subscription_id,
            amount=body.amount,
            currency=body.currency,
            paid_at=body.paid_at,
            period_start=body.period_start,
            period_end=body.period_end,
            status=_status(body.status),
            source=_source(body.source),
            notes=body.notes,
        )
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(p)


@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: UUID,
    user_id: CurrentUserId,
    service: PaymentRecordService = Depends(get_payment_record_service),
) -> dict[str, str]:
    try:
        await service.delete_payment(user_id, payment_id)
    except DomainError as exc:
        raise _map(exc) from exc
    return {"detail": "deleted", "code": "DELETED"}
