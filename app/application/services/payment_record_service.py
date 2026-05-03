"""Payment log orchestration."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.entities.payment import Payment, PaymentSource, PaymentStatus
from app.domain.exceptions import PaymentNotFoundError, SubscriptionNotFoundError
from app.domain.repositories.payment_repository import PaymentRepository
from app.domain.repositories.subscription_repository import SubscriptionRepository


class PaymentRecordService:
    """CRUD for recorded payments."""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        subscription_repository: SubscriptionRepository,
    ) -> None:
        self._pay = payment_repository
        self._subs = subscription_repository

    async def _ensure_subscription_owned(self, user_id: UUID, subscription_id: UUID | None) -> None:
        if subscription_id is None:
            return
        sub = await self._subs.get_for_user(user_id, subscription_id)
        if sub is None:
            raise SubscriptionNotFoundError()

    async def list_payments(
        self,
        user_id: UUID,
        *,
        skip: int,
        limit: int,
        subscription_id: UUID | None,
    ) -> tuple[list[Payment], int]:
        return await self._pay.list_for_user(
            user_id,
            skip=skip,
            limit=limit,
            subscription_id=subscription_id,
        )

    async def get_payment(self, user_id: UUID, payment_id: UUID) -> Payment:
        p = await self._pay.get_for_user(user_id, payment_id)
        if p is None:
            raise PaymentNotFoundError()
        return p

    async def create_payment(
        self,
        user_id: UUID,
        *,
        subscription_id: UUID | None,
        amount: Decimal,
        currency: str,
        paid_at: datetime,
        period_start: date | None,
        period_end: date | None,
        status: PaymentStatus,
        source: PaymentSource,
        notes: str | None,
    ) -> Payment:
        await self._ensure_subscription_owned(user_id, subscription_id)

        now = datetime.now(tz=UTC)
        entity = Payment(
            id=uuid4(),
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency.strip().upper(),
            paid_at=paid_at,
            period_start=period_start,
            period_end=period_end,
            status=status,
            source=source,
            notes=notes.strip() if notes else None,
            created_at=now,
            updated_at=now,
        )
        return await self._pay.create(entity)

    async def update_payment(
        self,
        user_id: UUID,
        payment_id: UUID,
        *,
        subscription_id: UUID | None,
        amount: Decimal,
        currency: str,
        paid_at: datetime,
        period_start: date | None,
        period_end: date | None,
        status: PaymentStatus,
        source: PaymentSource,
        notes: str | None,
    ) -> Payment:
        existing = await self.get_payment(user_id, payment_id)
        await self._ensure_subscription_owned(user_id, subscription_id)

        now = datetime.now(tz=UTC)
        updated = Payment(
            id=existing.id,
            user_id=existing.user_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency.strip().upper(),
            paid_at=paid_at,
            period_start=period_start,
            period_end=period_end,
            status=status,
            source=source,
            notes=notes.strip() if notes else None,
            created_at=existing.created_at,
            updated_at=now,
        )
        return await self._pay.update(updated)

    async def delete_payment(self, user_id: UUID, payment_id: UUID) -> None:
        ok = await self._pay.delete(user_id, payment_id)
        if not ok:
            raise PaymentNotFoundError()
