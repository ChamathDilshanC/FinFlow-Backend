"""Expense transaction persistence port."""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities.transaction import Transaction


class TransactionRepository(Protocol):
    """Owner-scoped ledger access."""

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        skip: int,
        limit: int,
        category_id: UUID | None,
        from_occurred: datetime | None,
        to_occurred: datetime | None,
    ) -> tuple[list[Transaction], int]:
        """Paginated transactions with optional filters."""

    async def get_for_user(self, user_id: UUID, transaction_id: UUID) -> Transaction | None:
        """Load transaction owned by user."""

    async def sum_amount_for_user_period(
        self,
        user_id: UUID,
        *,
        from_occurred: datetime,
        to_occurred: datetime,
    ) -> float:
        """Sum amounts (same currency assumed by caller)."""

    async def create(self, transaction: Transaction) -> Transaction:
        """Insert transaction."""

    async def update(self, transaction: Transaction) -> Transaction:
        """Update transaction."""

    async def delete(self, user_id: UUID, transaction_id: UUID) -> bool:
        """Delete owned transaction."""
