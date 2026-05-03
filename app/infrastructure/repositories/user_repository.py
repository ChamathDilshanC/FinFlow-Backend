"""
SQLAlchemy implementation of :class:`app.domain.repositories.user_repository.UserRepository`.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.infrastructure.database.models.user import UserModel


def _to_entity(row: UserModel) -> User:
    """Map ORM row to domain user."""
    return User(
        id=row.id,
        email=row.email,
        hashed_password=row.hashed_password,
        monthly_budget=row.monthly_budget,
        default_currency=row.default_currency,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyUserRepository:
    """
    Persists users via SQLAlchemy async sessions.

    Args:
        session: Request-scoped async session (injected per operation batch).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Load user by id; returns ``None`` when missing."""
        result = await self._session.get(UserModel, user_id)
        return _to_entity(result) if result else None

    async def get_by_email(self, email: str) -> User | None:
        """Load user by email using case-insensitive match."""
        stmt = select(UserModel).where(func.lower(UserModel.email) == email.strip().lower())
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def create(self, user: User) -> User:
        """Insert a new ``users`` row from a domain entity."""
        model = UserModel(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            monthly_budget=user.monthly_budget,
            default_currency=user.default_currency,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(self, user: User) -> User:
        """Update mutable columns for an existing user."""
        model = await self._session.get(UserModel, user.id)
        if model is None:
            return user
        model.email = user.email
        model.hashed_password = user.hashed_password
        model.monthly_budget = user.monthly_budget
        model.default_currency = user.default_currency
        model.updated_at = user.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
