"""Category entity for tagging subscriptions, expenses, or both."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class CategoryKind(StrEnum):
    """Where this category applies."""

    SUBSCRIPTION = "subscription"
    EXPENSE = "expense"
    BOTH = "both"


@dataclass(slots=True)
class Category:
    """User-defined bucket for analytics and budgets."""

    id: UUID
    user_id: UUID
    name: str
    icon: str | None
    color: str | None
    kind: CategoryKind
    created_at: datetime
    updated_at: datetime
