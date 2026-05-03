"""Exchange rate cache orchestration."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.entities.exchange_rate import ExchangeRate
from app.domain.exceptions import ExchangeRateNotFoundError
from app.domain.repositories.exchange_rate_repository import ExchangeRateRepository


class ExchangeRateService:
    """Manual FX quotes for reporting."""

    def __init__(self, exchange_rate_repository: ExchangeRateRepository) -> None:
        self._repo = exchange_rate_repository

    async def list_rates(
        self,
        *,
        from_date: date,
        to_date: date,
        base_currency: str | None,
    ) -> list[ExchangeRate]:
        return await self._repo.list_in_range(
            from_date=from_date,
            to_date=to_date,
            base_currency=base_currency,
        )

    async def upsert_rate(
        self,
        *,
        rate_date: date,
        base_currency: str,
        quote_currency: str,
        rate: Decimal,
    ) -> ExchangeRate:
        now = datetime.now(tz=UTC)
        entity = ExchangeRate(
            id=uuid4(),
            rate_date=rate_date,
            base_currency=base_currency.upper(),
            quote_currency=quote_currency.upper(),
            rate=rate,
            created_at=now,
        )
        return await self._repo.upsert(entity)

    async def delete_rate(self, rate_id: UUID) -> None:
        ok = await self._repo.delete(rate_id)
        if not ok:
            raise ExchangeRateNotFoundError()
