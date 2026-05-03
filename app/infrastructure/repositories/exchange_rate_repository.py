"""SQLAlchemy exchange rate cache."""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.exchange_rate import ExchangeRate
from app.infrastructure.database.models.exchange_rate import ExchangeRateModel


def _to_entity(row: ExchangeRateModel) -> ExchangeRate:
    return ExchangeRate(
        id=row.id,
        rate_date=row.rate_date,
        base_currency=row.base_currency,
        quote_currency=row.quote_currency,
        rate=row.rate,
        created_at=row.created_at,
    )


class SqlAlchemyExchangeRateRepository:
    """FX quote storage."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_in_range(
        self,
        *,
        from_date: date,
        to_date: date,
        base_currency: str | None,
    ) -> list[ExchangeRate]:
        filters = [
            ExchangeRateModel.rate_date >= from_date,
            ExchangeRateModel.rate_date <= to_date,
        ]
        if base_currency is not None:
            filters.append(ExchangeRateModel.base_currency == base_currency.upper())
        stmt = (
            select(ExchangeRateModel)
            .where(and_(*filters))
            .order_by(ExchangeRateModel.rate_date.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def upsert(self, rate: ExchangeRate) -> ExchangeRate:
        stmt = select(ExchangeRateModel).where(
            and_(
                ExchangeRateModel.rate_date == rate.rate_date,
                ExchangeRateModel.base_currency == rate.base_currency.upper(),
                ExchangeRateModel.quote_currency == rate.quote_currency.upper(),
            ),
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is None:
            model = ExchangeRateModel(
                id=rate.id,
                rate_date=rate.rate_date,
                base_currency=rate.base_currency.upper(),
                quote_currency=rate.quote_currency.upper(),
                rate=rate.rate,
                created_at=rate.created_at,
            )
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            return _to_entity(model)

        existing.rate = rate.rate
        await self._session.flush()
        await self._session.refresh(existing)
        return _to_entity(existing)

    async def delete(self, rate_id: UUID) -> bool:
        model = await self._session.get(ExchangeRateModel, rate_id)
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
