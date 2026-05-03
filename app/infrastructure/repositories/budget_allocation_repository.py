"""SQLAlchemy budget allocation repository."""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.budget_allocation import BudgetAllocation
from app.infrastructure.database.models.budget_allocation import BudgetAllocationModel


def _to_entity(row: BudgetAllocationModel) -> BudgetAllocation:
    return BudgetAllocation(
        id=row.id,
        user_id=row.user_id,
        category_id=row.category_id,
        budget_month=row.budget_month,
        limit_amount=row.limit_amount,
        currency=row.currency,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyBudgetAllocationRepository:
    """Monthly category caps."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: UUID, *, skip: int, limit: int) -> tuple[list[BudgetAllocation], int]:
        base = BudgetAllocationModel.user_id == user_id
        count_stmt = select(func.count()).select_from(BudgetAllocationModel).where(base)
        total = int((await self._session.execute(count_stmt)).scalar_one())
        page_stmt = (
            select(BudgetAllocationModel)
            .where(base)
            .order_by(BudgetAllocationModel.budget_month.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = (await self._session.execute(page_stmt)).scalars().all()
        return ([_to_entity(r) for r in rows], total)

    async def list_for_month(self, user_id: UUID, budget_month: date) -> list[BudgetAllocation]:
        stmt = select(BudgetAllocationModel).where(
            and_(
                BudgetAllocationModel.user_id == user_id,
                BudgetAllocationModel.budget_month == budget_month,
            ),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(r) for r in rows]

    async def get_for_user(self, user_id: UUID, budget_id: UUID) -> BudgetAllocation | None:
        stmt = select(BudgetAllocationModel).where(
            and_(BudgetAllocationModel.id == budget_id, BudgetAllocationModel.user_id == user_id),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def create(self, row: BudgetAllocation) -> BudgetAllocation:
        model = BudgetAllocationModel(
            id=row.id,
            user_id=row.user_id,
            category_id=row.category_id,
            budget_month=row.budget_month,
            limit_amount=row.limit_amount,
            currency=row.currency,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(self, row: BudgetAllocation) -> BudgetAllocation:
        model = await self._session.get(BudgetAllocationModel, row.id)
        if model is None or model.user_id != row.user_id:
            return row
        model.category_id = row.category_id
        model.budget_month = row.budget_month
        model.limit_amount = row.limit_amount
        model.currency = row.currency
        model.updated_at = row.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, user_id: UUID, budget_id: UUID) -> bool:
        model = await self._session.get(BudgetAllocationModel, budget_id)
        if model is None or model.user_id != user_id:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
