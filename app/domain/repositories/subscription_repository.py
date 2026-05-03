"""
Subscription repository port for CRUD and scoped analytics queries.
"""

from typing import Protocol
from uuid import UUID

from app.domain.entities.subscription import Subscription


class SubscriptionRepository(Protocol):
    """Contract for subscription persistence and owner-scoped reads."""

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 50,
        active_only: bool | None = None,
    ) -> tuple[list[Subscription], int]:
        """
        Return a page of subscriptions for a user and total count.

        Args:
            user_id: Owner user id.
            skip: Pagination offset.
            limit: Maximum rows to return (caller validates bounds).
            active_only: If set, filter ``is_active`` to that value.

        Returns:
            Tuple of (items for page, total matching rows).
        """

    async def get_for_user(self, user_id: UUID, subscription_id: UUID) -> Subscription | None:
        """
        Load a subscription ensuring it belongs to ``user_id``.

        Args:
            user_id: Authenticated user id.
            subscription_id: Subscription primary key.

        Returns:
            Entity if owned by user; otherwise ``None``.
        """

    async def create(self, subscription: Subscription) -> Subscription:
        """Insert a subscription row."""

    async def update(self, subscription: Subscription) -> Subscription:
        """Update an existing subscription row."""

    async def delete(self, user_id: UUID, subscription_id: UUID) -> bool:
        """
        Delete a subscription owned by ``user_id``.

        Returns:
            ``True`` if a row was deleted.
        """

    async def list_active_for_user(self, user_id: UUID) -> list[Subscription]:
        """
        Return all **active** subscriptions for dashboard aggregation.

        Not paginated; used for analytics that require a full in-memory rollup in
        the application layer (monthly-equivalent totals, category breakdown).
        """
