"""One-off or recurring expense ledger row."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class Transaction:
    """Expense transaction linked optionally to a category."""

    id: UUID
    user_id: UUID
    category_id: UUID | None
    amount: Decimal
    currency: str
    occurred_at: datetime
    merchant: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
