"""FX rate cache persistence port."""

from datetime import date
from typing import Protocol
from uuid import UUID

from app.domain.entities.exchange_rate import ExchangeRate


class ExchangeRateRepository(Protocol):
    """Stored exchange rates for reporting."""

    async def list_in_range(
        self,
        *,
        from_date: date,
        to_date: date,
        base_currency: str | None,
    ) -> list[ExchangeRate]:
        """Return rates in date range, optionally filtered by base."""

    async def upsert(self, rate: ExchangeRate) -> ExchangeRate:
        """Insert or replace by (date, base, quote)."""

    async def delete(self, rate_id: UUID) -> bool:
        """Delete by primary key."""
