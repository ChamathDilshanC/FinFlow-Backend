"""Expense transaction orchestration."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.entities.transaction import Transaction
from app.domain.exceptions import CategoryNotFoundError, TransactionNotFoundError
from app.domain.repositories.category_repository import CategoryRepository
from app.domain.repositories.transaction_repository import TransactionRepository


class TransactionService:
    """Ledger use cases."""

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        category_repository: CategoryRepository,
    ) -> None:
        self._tx = transaction_repository
        self._categories = category_repository

    async def list_transactions(
        self,
        user_id: UUID,
        *,
        skip: int,
        limit: int,
        category_id: UUID | None,
        from_occurred: datetime | None,
        to_occurred: datetime | None,
    ) -> tuple[list[Transaction], int]:
        return await self._tx.list_for_user(
            user_id,
            skip=skip,
            limit=limit,
            category_id=category_id,
            from_occurred=from_occurred,
            to_occurred=to_occurred,
        )

    async def get_transaction(self, user_id: UUID, transaction_id: UUID) -> Transaction:
        t = await self._tx.get_for_user(user_id, transaction_id)
        if t is None:
            raise TransactionNotFoundError()
        return t

    async def create_transaction(
        self,
        user_id: UUID,
        *,
        category_id: UUID | None,
        amount: Decimal,
        currency: str,
        occurred_at: datetime,
        merchant: str | None,
        notes: str | None,
    ) -> Transaction:
        if category_id is not None:
            cat = await self._categories.get_for_user(user_id, category_id)
            if cat is None:
                raise CategoryNotFoundError()
        now = datetime.now(tz=UTC)
        entity = Transaction(
            id=uuid4(),
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            currency=currency.strip().upper(),
            occurred_at=occurred_at,
            merchant=merchant.strip() if merchant else None,
            notes=notes.strip() if notes else None,
            created_at=now,
            updated_at=now,
        )
        return await self._tx.create(entity)

    async def update_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
        *,
        category_id: UUID | None,
        amount: Decimal,
        currency: str,
        occurred_at: datetime,
        merchant: str | None,
        notes: str | None,
    ) -> Transaction:
        existing = await self.get_transaction(user_id, transaction_id)
        if category_id is not None:
            cat = await self._categories.get_for_user(user_id, category_id)
            if cat is None:
                raise CategoryNotFoundError()
        now = datetime.now(tz=UTC)
        updated = Transaction(
            id=existing.id,
            user_id=existing.user_id,
            category_id=category_id,
            amount=amount,
            currency=currency.strip().upper(),
            occurred_at=occurred_at,
            merchant=merchant.strip() if merchant else None,
            notes=notes.strip() if notes else None,
            created_at=existing.created_at,
            updated_at=now,
        )
        return await self._tx.update(updated)

    async def delete_transaction(self, user_id: UUID, transaction_id: UUID) -> None:
        ok = await self._tx.delete(user_id, transaction_id)
        if not ok:
            raise TransactionNotFoundError()
