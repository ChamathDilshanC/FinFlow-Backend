"""Recorded payment against a subscription or ad-hoc charge."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class PaymentStatus(StrEnum):
    """Lifecycle of a payment record."""

    PAID = "paid"
    PENDING = "pending"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentSource(StrEnum):
    """How the row was created."""

    MANUAL = "manual"
    IMPORT = "import"
    SYSTEM = "system"


@dataclass(slots=True)
class Payment:
    """Subscription charge or manual payment log."""

    id: UUID
    user_id: UUID
    subscription_id: UUID | None
    amount: Decimal
    currency: str
    paid_at: datetime
    period_start: date | None
    period_end: date | None
    status: PaymentStatus
    source: PaymentSource
    notes: str | None
    created_at: datetime
    updated_at: datetime
