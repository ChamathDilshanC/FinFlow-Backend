"""Category CRUD."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.v1.dependencies import CurrentUserId, get_category_service
from app.api.v1.schemas.categories import CategoryCreate, CategoryKindSchema, CategoryResponse, CategoryUpdate
from app.application.services.category_service import CategoryService
from app.core.exceptions import AppHTTPException
from app.domain.entities.category import CategoryKind
from app.domain.exceptions import CategoryNotFoundError, DomainError


router = APIRouter()


def _map(exc: DomainError) -> AppHTTPException:
    if isinstance(exc, CategoryNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    return AppHTTPException(detail=exc.message, code=exc.code, status_code=400)


def _kind(s: CategoryKindSchema) -> CategoryKind:
    return CategoryKind(s.value)


def _resp(c) -> CategoryResponse:
    return CategoryResponse(
        id=c.id,
        user_id=c.user_id,
        name=c.name,
        icon=c.icon,
        color=c.color,
        kind=CategoryKindSchema(c.kind.value),
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    response: Response,
    user_id: CurrentUserId,
    service: CategoryService = Depends(get_category_service),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[CategoryResponse]:
    items, total = await service.list_categories(user_id, skip=skip, limit=limit)
    response.headers["X-Total-Count"] = str(total)
    return [_resp(c) for c in items]


@router.post("", response_model=CategoryResponse)
async def create_category(
    body: CategoryCreate,
    user_id: CurrentUserId,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    try:
        c = await service.create_category(
            user_id,
            name=body.name,
            icon=body.icon,
            color=body.color,
            kind=_kind(body.kind),
        )
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(c)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    user_id: CurrentUserId,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    try:
        c = await service.get_category(user_id, category_id)
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(c)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    body: CategoryUpdate,
    user_id: CurrentUserId,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    try:
        c = await service.update_category(
            user_id,
            category_id,
            name=body.name,
            icon=body.icon,
            color=body.color,
            kind=_kind(body.kind),
        )
    except DomainError as exc:
        raise _map(exc) from exc
    return _resp(c)


@router.delete("/{category_id}")
async def delete_category(
    category_id: UUID,
    user_id: CurrentUserId,
    service: CategoryService = Depends(get_category_service),
) -> dict[str, str]:
    try:
        await service.delete_category(user_id, category_id)
    except DomainError as exc:
        raise _map(exc) from exc
    return {"detail": "deleted", "code": "DELETED"}
