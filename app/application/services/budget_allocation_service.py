"""Monthly category budget orchestration."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.entities.budget_allocation import BudgetAllocation
from app.domain.exceptions import BudgetNotFoundError, CategoryNotFoundError
from app.domain.repositories.budget_allocation_repository import BudgetAllocationRepository
from app.domain.repositories.category_repository import CategoryRepository


def first_day_of_month(d: date) -> date:
    """Normalize to the first calendar day of the same month."""
    return date(d.year, d.month, 1)


class BudgetAllocationService:
    """Per-category monthly caps."""

    def __init__(
        self,
        budget_repository: BudgetAllocationRepository,
        category_repository: CategoryRepository,
    ) -> None:
        self._budget = budget_repository
        self._categories = category_repository

    async def list_budgets(self, user_id: UUID, *, skip: int, limit: int) -> tuple[list[BudgetAllocation], int]:
        return await self._budget.list_for_user(user_id, skip=skip, limit=limit)

    async def get_budget(self, user_id: UUID, budget_id: UUID) -> BudgetAllocation:
        b = await self._budget.get_for_user(user_id, budget_id)
        if b is None:
            raise BudgetNotFoundError()
        return b

    async def create_budget(
        self,
        user_id: UUID,
        *,
        category_id: UUID,
        budget_month: date,
        limit_amount: Decimal,
        currency: str,
    ) -> BudgetAllocation:
        cat = await self._categories.get_for_user(user_id, category_id)
        if cat is None:
            raise CategoryNotFoundError()
        month_key = first_day_of_month(budget_month)
        now = datetime.now(tz=UTC)
        entity = BudgetAllocation(
            id=uuid4(),
            user_id=user_id,
            category_id=category_id,
            budget_month=month_key,
            limit_amount=limit_amount,
            currency=currency.strip().upper(),
            created_at=now,
            updated_at=now,
        )
        return await self._budget.create(entity)

    async def update_budget(
        self,
        user_id: UUID,
        budget_id: UUID,
        *,
        category_id: UUID,
        budget_month: date,
        limit_amount: Decimal,
        currency: str,
    ) -> BudgetAllocation:
        existing = await self.get_budget(user_id, budget_id)
        cat = await self._categories.get_for_user(user_id, category_id)
        if cat is None:
            raise CategoryNotFoundError()
        now = datetime.now(tz=UTC)
        updated = BudgetAllocation(
            id=existing.id,
            user_id=existing.user_id,
            category_id=category_id,
            budget_month=first_day_of_month(budget_month),
            limit_amount=limit_amount,
            currency=currency.strip().upper(),
            created_at=existing.created_at,
            updated_at=now,
        )
        return await self._budget.update(updated)

    async def delete_budget(self, user_id: UUID, budget_id: UUID) -> None:
        ok = await self._budget.delete(user_id, budget_id)
        if not ok:
            raise BudgetNotFoundError()
