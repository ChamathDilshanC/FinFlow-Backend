"""Cached exchange rates (manual admin / import)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import CurrentUserId, get_exchange_rate_service
from app.api.v1.schemas.exchange_rates import ExchangeRateResponse, ExchangeRateUpsert
from app.application.services.exchange_rate_service import ExchangeRateService
from app.core.exceptions import AppHTTPException
from app.domain.exceptions import DomainError, ExchangeRateNotFoundError


router = APIRouter()


def _map(exc: DomainError) -> AppHTTPException:
    if isinstance(exc, ExchangeRateNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    return AppHTTPException(detail=exc.message, code=exc.code, status_code=400)


def _resp(r) -> ExchangeRateResponse:
    return ExchangeRateResponse(
        id=r.id,
        rate_date=r.rate_date,
        base_currency=r.base_currency,
        quote_currency=r.quote_currency,
        rate=r.rate,
        created_at=r.created_at,
    )


@router.get("", response_model=list[ExchangeRateResponse])
async def list_exchange_rates(
    user_id: CurrentUserId,
    service: ExchangeRateService = Depends(get_exchange_rate_service),
    from_date: date = Query(..., description="Start (inclusive)"),
    to_date: date = Query(..., description="End (inclusive)"),
    base_currency: str | None = Query(None, min_length=3, max_length=3),
) -> list[ExchangeRateResponse]:
    rows = await service.list_rates(
        from_date=from_date,
        to_date=to_date,
        base_currency=base_currency.upper() if base_currency else None,
    )
    return [_resp(r) for r in rows]


@router.post("", response_model=ExchangeRateResponse)
async def upsert_exchange_rate(
    body: ExchangeRateUpsert,
    user_id: CurrentUserId,
    service: ExchangeRateService = Depends(get_exchange_rate_service),
) -> ExchangeRateResponse:
    r = await service.upsert_rate(
        rate_date=body.rate_date,
        base_currency=body.base_currency,
        quote_currency=body.quote_currency,
        rate=body.rate,
    )
    return _resp(r)


@router.delete("/{rate_id}")
async def delete_exchange_rate(
    rate_id: UUID,
    user_id: CurrentUserId,
    service: ExchangeRateService = Depends(get_exchange_rate_service),
) -> dict[str, str]:
    try:
        await service.delete_rate(rate_id)
    except DomainError as exc:
        raise _map(exc) from exc
    return {"detail": "deleted", "code": "DELETED"}
