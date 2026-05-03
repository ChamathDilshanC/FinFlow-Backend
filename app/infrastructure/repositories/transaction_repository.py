"""SQLAlchemy transaction repository."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.transaction import Transaction
from app.infrastructure.database.models.transaction import TransactionModel


def _to_entity(row: TransactionModel) -> Transaction:
    return Transaction(
        id=row.id,
        user_id=row.user_id,
        category_id=row.category_id,
        amount=row.amount,
        currency=row.currency,
        occurred_at=row.occurred_at,
        merchant=row.merchant,
        notes=row.notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyTransactionRepository:
    """Expense ledger persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        filters = [TransactionModel.user_id == user_id]
        if category_id is not None:
            filters.append(TransactionModel.category_id == category_id)
        if from_occurred is not None:
            filters.append(TransactionModel.occurred_at >= from_occurred)
        if to_occurred is not None:
            filters.append(TransactionModel.occurred_at <= to_occurred)

        base_filter = and_(*filters)
        count_stmt = select(func.count()).select_from(TransactionModel).where(base_filter)
        total = int((await self._session.execute(count_stmt)).scalar_one())

        page_stmt = (
            select(TransactionModel)
            .where(base_filter)
            .order_by(TransactionModel.occurred_at.desc())
            .offset(skip)
            .limit(limit)
        )
        rows = (await self._session.execute(page_stmt)).scalars().all()
        return ([_to_entity(r) for r in rows], total)

    async def get_for_user(self, user_id: UUID, transaction_id: UUID) -> Transaction | None:
        stmt = select(TransactionModel).where(
            and_(TransactionModel.id == transaction_id, TransactionModel.user_id == user_id),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def sum_amount_for_user_period(
        self,
        user_id: UUID,
        *,
        from_occurred: datetime,
        to_occurred: datetime,
    ) -> float:
        stmt = select(func.coalesce(func.sum(TransactionModel.amount), 0)).where(
            and_(
                TransactionModel.user_id == user_id,
                TransactionModel.occurred_at >= from_occurred,
                TransactionModel.occurred_at <= to_occurred,
            ),
        )
        val = (await self._session.execute(stmt)).scalar_one()
        return float(val)

    async def create(self, transaction: Transaction) -> Transaction:
        model = TransactionModel(
            id=transaction.id,
            user_id=transaction.user_id,
            category_id=transaction.category_id,
            amount=transaction.amount,
            currency=transaction.currency,
            occurred_at=transaction.occurred_at,
            merchant=transaction.merchant,
            notes=transaction.notes,
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(self, transaction: Transaction) -> Transaction:
        model = await self._session.get(TransactionModel, transaction.id)
        if model is None or model.user_id != transaction.user_id:
            return transaction
        model.category_id = transaction.category_id
        model.amount = transaction.amount
        model.currency = transaction.currency
        model.occurred_at = transaction.occurred_at
        model.merchant = transaction.merchant
        model.notes = transaction.notes
        model.updated_at = transaction.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, user_id: UUID, transaction_id: UUID) -> bool:
        model = await self._session.get(TransactionModel, transaction_id)
        if model is None or model.user_id != user_id:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
