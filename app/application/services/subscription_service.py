"""
Subscription CRUD with pagination and owner-scoped access rules.

All persistence happens through :class:`SubscriptionRepository` implementations.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.application.finance import monthly_equivalent
from app.domain.entities.subscription import BillingCycle, Subscription
from app.domain.exceptions import SubscriptionNotFoundError
from app.domain.repositories.subscription_repository import SubscriptionRepository


@dataclass(slots=True)
class PaginatedSubscriptions:
    """Page descriptor for list endpoints."""

    items: list[Subscription]
    total: int
    skip: int
    limit: int


class SubscriptionService:
    """
    Owner-scoped subscription lifecycle and monthly-limit tracking hints.

    Args:
        subscription_repository: Persistence adapter for subscriptions.
    """

    def __init__(self, subscription_repository: SubscriptionRepository) -> None:
        self._subs = subscription_repository

    async def list_subscriptions(
        self,
        user_id: UUID,
        *,
        skip: int,
        limit: int,
        active_only: bool | None = None,
    ) -> PaginatedSubscriptions:
        """
        List subscriptions with pagination metadata.

        Args:
            user_id: Authenticated user id.
            skip: OFFSET clause value (non-negative).
            limit: LIMIT clause value (positive, capped by API layer).
            active_only: Optional filter on ``is_active``.

        Returns:
            Items page plus total count for UI pagination controls.
        """
        items, total = await self._subs.list_for_user(
            user_id,
            skip=skip,
            limit=limit,
            active_only=active_only,
        )
        return PaginatedSubscriptions(items=items, total=total, skip=skip, limit=limit)

    async def get_subscription(self, user_id: UUID, subscription_id: UUID) -> Subscription:
        """
        Fetch a single subscription when owned by ``user_id``.

        Raises:
            SubscriptionNotFoundError: When missing or not owned.
        """
        sub = await self._subs.get_for_user(user_id, subscription_id)
        if sub is None:
            raise SubscriptionNotFoundError()
        return sub

    async def create_subscription(
        self,
        user_id: UUID,
        *,
        name: str,
        amount: Decimal,
        currency: str,
        billing_cycle: BillingCycle,
        category: str | None,
        monthly_limit: Decimal | None,
        start_date: date,
        next_renewal_date: date | None,
        is_active: bool,
        notes: str | None,
    ) -> Subscription:
        """
        Create a subscription row after validating limit semantics.

        If ``monthly_limit`` is provided, it must be >= monthly-equivalent spend
        derived from ``amount`` and ``billing_cycle`` (business guardrail).
        """
        me = monthly_equivalent(amount, billing_cycle)
        if monthly_limit is not None and monthly_limit < me:
            msg = "monthly_limit cannot be less than monthly-equivalent spend"
            raise ValueError(msg)

        now = datetime.now(tz=UTC)
        entity = Subscription(
            id=uuid4(),
            user_id=user_id,
            name=name.strip(),
            amount=amount,
            currency=currency.strip().upper(),
            billing_cycle=billing_cycle,
            category=category.strip() if category else None,
            monthly_limit=monthly_limit,
            start_date=start_date,
            next_renewal_date=next_renewal_date,
            is_active=is_active,
            notes=notes.strip() if notes else None,
            created_at=now,
            updated_at=now,
        )
        return await self._subs.create(entity)

    async def update_subscription(
        self,
        user_id: UUID,
        subscription_id: UUID,
        *,
        name: str,
        amount: Decimal,
        currency: str,
        billing_cycle: BillingCycle,
        category: str | None,
        monthly_limit: Decimal | None,
        start_date: date,
        next_renewal_date: date | None,
        is_active: bool,
        notes: str | None,
    ) -> Subscription:
        """Update fields on an owned subscription with the same limit validation."""
        existing = await self.get_subscription(user_id, subscription_id)
        me = monthly_equivalent(amount, billing_cycle)
        if monthly_limit is not None and monthly_limit < me:
            msg = "monthly_limit cannot be less than monthly-equivalent spend"
            raise ValueError(msg)

        now = datetime.now(tz=UTC)
        updated = Subscription(
            id=existing.id,
            user_id=existing.user_id,
            name=name.strip(),
            amount=amount,
            currency=currency.strip().upper(),
            billing_cycle=billing_cycle,
            category=category.strip() if category else None,
            monthly_limit=monthly_limit,
            start_date=start_date,
            next_renewal_date=next_renewal_date,
            is_active=is_active,
            notes=notes.strip() if notes else None,
            created_at=existing.created_at,
            updated_at=now,
        )
        return await self._subs.update(updated)

    async def delete_subscription(self, user_id: UUID, subscription_id: UUID) -> None:
        """Delete an owned subscription or raise :class:`SubscriptionNotFoundError`."""
        deleted = await self._subs.delete(user_id, subscription_id)
        if not deleted:
            raise SubscriptionNotFoundError()
