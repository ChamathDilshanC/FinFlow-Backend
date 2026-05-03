"""Budget allocation persistence port."""

from datetime import date
from typing import Protocol
from uuid import UUID

from app.domain.entities.budget_allocation import BudgetAllocation


class BudgetAllocationRepository(Protocol):
    """Per-category monthly caps."""

    async def list_for_user(self, user_id: UUID, *, skip: int, limit: int) -> tuple[list[BudgetAllocation], int]:
        """Paginated budgets."""

    async def list_for_month(self, user_id: UUID, budget_month: date) -> list[BudgetAllocation]:
        """All category budgets for the given month (first-of-month date)."""

    async def get_for_user(self, user_id: UUID, budget_id: UUID) -> BudgetAllocation | None:
        """Load budget owned by user."""

    async def create(self, row: BudgetAllocation) -> BudgetAllocation:
        """Insert budget row."""

    async def update(self, row: BudgetAllocation) -> BudgetAllocation:
        """Update budget row."""

    async def delete(self, user_id: UUID, budget_id: UUID) -> bool:
        """Delete owned budget."""
