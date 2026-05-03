"""Category persistence port."""

from typing import Protocol
from uuid import UUID

from app.domain.entities.category import Category


class CategoryRepository(Protocol):
    """Owner-scoped category CRUD."""

    async def list_for_user(self, user_id: UUID, *, skip: int, limit: int) -> tuple[list[Category], int]:
        """Paginated categories."""

    async def get_for_user(self, user_id: UUID, category_id: UUID) -> Category | None:
        """Load category when owned by user."""

    async def create(self, category: Category) -> Category:
        """Insert category."""

    async def update(self, category: Category) -> Category:
        """Update category."""

    async def delete(self, user_id: UUID, category_id: UUID) -> bool:
        """Delete owned category."""
