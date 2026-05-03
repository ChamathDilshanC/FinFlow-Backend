"""
Subscription entity modeling recurring spend.

Billing cycles drive normalized monthly amounts for budgets and summaries.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID


class BillingCycle(StrEnum):
    """Supported recurrence patterns for subscription charges."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass(slots=True)
class Subscription:
    """
    Recurring payment owned by a user.

    Attributes:
        id: Primary key.
        user_id: Owning user foreign key.
        name: Display name (e.g. ``Netflix``).
        amount: Charge amount in ``currency`` per billing cycle.
        currency: ISO 4217 code (e.g. ``USD``).
        billing_cycle: How often ``amount`` is charged.
        category: Free-form grouping for analytics (e.g. ``streaming``).
        monthly_limit: Optional cap for this subscription in monthly-equivalent terms.
        start_date: When the subscription began.
        next_renewal_date: Expected next charge date (nullable if unknown).
        is_active: Whether the subscription is currently counted toward totals.
        notes: Optional context for the user.
        created_at: Insert timestamp (UTC).
        updated_at: Last update timestamp (UTC).
    """

    id: UUID
    user_id: UUID
    name: str
    amount: Decimal
    currency: str
    billing_cycle: BillingCycle
    category: str | None
    monthly_limit: Decimal | None
    start_date: date
    next_renewal_date: date | None
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
