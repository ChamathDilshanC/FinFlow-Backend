"""
SQLAlchemy implementation of subscription persistence.
"""

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.subscription import BillingCycle, Subscription
from app.infrastructure.database.models.subscription import SubscriptionModel


def _to_entity(row: SubscriptionModel) -> Subscription:
    """Map ORM row to domain subscription."""
    return Subscription(
        id=row.id,
        user_id=row.user_id,
        name=row.name,
        amount=row.amount,
        currency=row.currency,
        billing_cycle=BillingCycle(row.billing_cycle),
        category=row.category,
        monthly_limit=row.monthly_limit,
        start_date=row.start_date,
        next_renewal_date=row.next_renewal_date,
        is_active=row.is_active,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemySubscriptionRepository:
    """
    Subscription CRUD using SQLAlchemy async queries only (no business rules).

    Args:
        session: Request-scoped async session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 50,
        active_only: bool | None = None,
    ) -> tuple[list[Subscription], int]:
        """Return paginated subscriptions plus total count for the owner."""
        filters = [SubscriptionModel.user_id == user_id]
        if active_only is True:
            filters.append(SubscriptionModel.is_active.is_(True))
        elif active_only is False:
            filters.append(SubscriptionModel.is_active.is_(False))

        count_stmt = select(func.count()).select_from(SubscriptionModel).where(and_(*filters))
        total = int((await self._session.execute(count_stmt)).scalar_one())

        page_stmt = (
            select(SubscriptionModel)
            .where(and_(*filters))
            .order_by(SubscriptionModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = (await self._session.execute(page_stmt)).scalars().all()
        return ([_to_entity(r) for r in rows], total)

    async def get_for_user(self, user_id: UUID, subscription_id: UUID) -> Subscription | None:
        """Return subscription when owned by ``user_id``."""
        stmt = select(SubscriptionModel).where(
            and_(
                SubscriptionModel.id == subscription_id,
                SubscriptionModel.user_id == user_id,
            )
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def create(self, subscription: Subscription) -> Subscription:
        """Insert subscription row."""
        model = SubscriptionModel(
            id=subscription.id,
            user_id=subscription.user_id,
            name=subscription.name,
            amount=subscription.amount,
            currency=subscription.currency,
            billing_cycle=subscription.billing_cycle.value,
            category=subscription.category,
            monthly_limit=subscription.monthly_limit,
            start_date=subscription.start_date,
            next_renewal_date=subscription.next_renewal_date,
            is_active=subscription.is_active,
            notes=subscription.notes,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(self, subscription: Subscription) -> Subscription:
        """Update mutable subscription fields."""
        model = await self._session.get(SubscriptionModel, subscription.id)
        if model is None or model.user_id != subscription.user_id:
            return subscription
        model.name = subscription.name
        model.amount = subscription.amount
        model.currency = subscription.currency
        model.billing_cycle = subscription.billing_cycle.value
        model.category = subscription.category
        model.monthly_limit = subscription.monthly_limit
        model.start_date = subscription.start_date
        model.next_renewal_date = subscription.next_renewal_date
        model.is_active = subscription.is_active
        model.notes = subscription.notes
        model.updated_at = subscription.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, user_id: UUID, subscription_id: UUID) -> bool:
        """Delete by id when owned by ``user_id``."""
        model = await self._session.get(SubscriptionModel, subscription_id)
        if model is None or model.user_id != user_id:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def list_active_for_user(self, user_id: UUID) -> list[Subscription]:
        """All active subscriptions for analytics."""
        stmt = (
            select(SubscriptionModel)
            .where(
                and_(
                    SubscriptionModel.user_id == user_id,
                    SubscriptionModel.is_active.is_(True),
                )
            )
            .order_by(SubscriptionModel.name.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]
