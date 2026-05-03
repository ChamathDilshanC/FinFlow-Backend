"""Monthly per-category spend cap."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class BudgetAllocation:
    """
    Limit for a category in a calendar month (``budget_month`` = first day of month).
    """

    id: UUID
    user_id: UUID
    category_id: UUID
    budget_month: date
    limit_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
