"""Category API schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryKindSchema(str, Enum):
    subscription = "subscription"
    expense = "expense"
    both = "both"


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    icon: str | None = Field(None, max_length=64)
    color: str | None = Field(None, max_length=32)
    kind: CategoryKindSchema = CategoryKindSchema.both


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    icon: str | None = Field(None, max_length=64)
    color: str | None = Field(None, max_length=32)
    kind: CategoryKindSchema


class CategoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    icon: str | None
    color: str | None
    kind: CategoryKindSchema
    created_at: datetime
    updated_at: datetime
