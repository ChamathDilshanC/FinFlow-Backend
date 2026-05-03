"""Category CRUD orchestration."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.entities.category import Category, CategoryKind
from app.domain.exceptions import CategoryNotFoundError
from app.domain.repositories.category_repository import CategoryRepository


class CategoryService:
    """Owner-scoped categories."""

    def __init__(self, category_repository: CategoryRepository) -> None:
        self._repo = category_repository

    async def list_categories(self, user_id: UUID, *, skip: int, limit: int) -> tuple[list[Category], int]:
        return await self._repo.list_for_user(user_id, skip=skip, limit=limit)

    async def get_category(self, user_id: UUID, category_id: UUID) -> Category:
        c = await self._repo.get_for_user(user_id, category_id)
        if c is None:
            raise CategoryNotFoundError()
        return c

    async def create_category(
        self,
        user_id: UUID,
        *,
        name: str,
        icon: str | None,
        color: str | None,
        kind: CategoryKind,
    ) -> Category:
        now = datetime.now(tz=UTC)
        entity = Category(
            id=uuid4(),
            user_id=user_id,
            name=name.strip(),
            icon=icon.strip() if icon else None,
            color=color.strip() if color else None,
            kind=kind,
            created_at=now,
            updated_at=now,
        )
        return await self._repo.create(entity)

    async def update_category(
        self,
        user_id: UUID,
        category_id: UUID,
        *,
        name: str,
        icon: str | None,
        color: str | None,
        kind: CategoryKind,
    ) -> Category:
        existing = await self.get_category(user_id, category_id)
        now = datetime.now(tz=UTC)
        updated = Category(
            id=existing.id,
            user_id=existing.user_id,
            name=name.strip(),
            icon=icon.strip() if icon else None,
            color=color.strip() if color else None,
            kind=kind,
            created_at=existing.created_at,
            updated_at=now,
        )
        return await self._repo.update(updated)

    async def delete_category(self, user_id: UUID, category_id: UUID) -> None:
        ok = await self._repo.delete(user_id, category_id)
        if not ok:
            raise CategoryNotFoundError()
