"""SQLAlchemy :class:`CategoryRepository` implementation."""

from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.category import Category, CategoryKind
from app.infrastructure.database.models.category import CategoryModel


def _to_entity(row: CategoryModel) -> Category:
    return Category(
        id=row.id,
        user_id=row.user_id,
        name=row.name,
        icon=row.icon,
        color=row.color,
        kind=CategoryKind(row.kind),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyCategoryRepository:
    """Category CRUD for a request-scoped session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: UUID, *, skip: int, limit: int) -> tuple[list[Category], int]:
        stmt_base = select(CategoryModel).where(CategoryModel.user_id == user_id)
        count_stmt = select(func.count()).select_from(CategoryModel).where(CategoryModel.user_id == user_id)
        total = int((await self._session.execute(count_stmt)).scalar_one())
        page_stmt = (
            stmt_base.order_by(CategoryModel.name.asc()).offset(skip).limit(limit)
        )
        rows = (await self._session.execute(page_stmt)).scalars().all()
        return ([_to_entity(r) for r in rows], total)

    async def get_for_user(self, user_id: UUID, category_id: UUID) -> Category | None:
        stmt = select(CategoryModel).where(
            and_(CategoryModel.id == category_id, CategoryModel.user_id == user_id),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def create(self, category: Category) -> Category:
        model = CategoryModel(
            id=category.id,
            user_id=category.user_id,
            name=category.name,
            icon=category.icon,
            color=category.color,
            kind=category.kind.value,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def update(self, category: Category) -> Category:
        model = await self._session.get(CategoryModel, category.id)
        if model is None or model.user_id != category.user_id:
            return category
        model.name = category.name
        model.icon = category.icon
        model.color = category.color
        model.kind = category.kind.value
        model.updated_at = category.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)

    async def delete(self, user_id: UUID, category_id: UUID) -> bool:
        model = await self._session.get(CategoryModel, category_id)
        if model is None or model.user_id != user_id:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
