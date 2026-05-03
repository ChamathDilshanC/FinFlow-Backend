"""SQLAlchemy payment repository."""

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.payment import Payment, PaymentSource, PaymentStatus
from app.infrastructure.database.models.payment import PaymentModel


def _to_entity(row: PaymentModel) -> Payment:
    return Payment(
        id=row.id,
        user_id=row.user_id,
        subscription_id=row.subscription_id,
        amount=row.amount,
        currency=row.currency,
        paid_at=row.paid_at,
        period_start=row.period_start,
        period_end=row.period_end,
        status=PaymentStatus(row.status),
        source=PaymentSource(row.source),
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyPaymentRepository:
    """Payment log persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        skip: int,
        limit: int,
        subscription_id: UUID | None,
    ) -> tuple[list[Payment], int]:
        filters = [PaymentModel.user_id == user_id]
        if subscription_id is not None:
            filters.append(PaymentModel.subscription_id == subscription_id)
        base_filter = and_(*filters)
        count_stmt = select(func.count()).select_from(PaymentModel).where(base_filter)
        total = int((await self._session.execute(count_stmt)).scalar_one())
        page_stmt = (
            select(PaymentModel)
            .where(base_filter)
            .order_by(PaymentModel.paid_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = (await self._session.execute(page_stmt)).scalars().all()
        return ([_to_entity(r) for r in rows], total)

    async def get_for_user(self, user_id: UUID, payment_id: UUID) -> Payment | None:
        stmt = select(PaymentModel).where(
            and_(PaymentModel.id == payment_id, PaymentModel.user_id == user_id),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def count_for_user(self, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(PaymentModel).where(PaymentModel.user_id == user_id)
        return int((await self._session.execute(stmt)).scalar_one())

    async def create(self, payment: Payment) -> Payment:
        model = PaymentModel(
            id=payment.id,
            user_id=payment.user_id,
            subscription_id=payment.subscription_id,
            amount=payment.amount,
            currency=payment.currency,
            paid_at=payment.paid_at,
            period_start=payment.period_start,
            period_end=payment.period_end,
            status=payment.status.value,
            source=payment.source.value,
            notes=payment.notes,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(self, payment: Payment) -> Payment:
        model = await self._session.get(PaymentModel, payment.id)
        if model is None or model.user_id != payment.user_id:
            return payment
        model.subscription_id = payment.subscription_id
        model.amount = payment.amount
        model.currency = payment.currency
        model.paid_at = payment.paid_at
        model.period_start = payment.period_start
        model.period_end = payment.period_end
        model.status = payment.status.value
        model.source = payment.source.value
        model.notes = payment.notes
        model.updated_at = payment.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, user_id: UUID, payment_id: UUID) -> bool:
        model = await self._session.get(PaymentModel, payment_id)
        if model is None or model.user_id != user_id:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
