"""Subscription CRUD DTOs."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class BillingCycleSchema(str, Enum):
    """Mirrors :class:`app.domain.entities.subscription.BillingCycle`."""

    weekly = "weekly"
    monthly = "monthly"
    quarterly = "quarterly"
    yearly = "yearly"


class SubscriptionCreate(BaseModel):
    """Create subscription body."""

    name: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, default="USD")
    billing_cycle: BillingCycleSchema
    category: str | None = Field(default=None, max_length=120)
    monthly_limit: Decimal | None = Field(default=None, ge=0)
    start_date: date
    next_renewal_date: date | None = None
    is_active: bool = True
    notes: str | None = Field(default=None, max_length=4000)


class SubscriptionUpdate(BaseModel):
    """Full replacement-style update body (same fields as create)."""

    name: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    billing_cycle: BillingCycleSchema
    category: str | None = Field(default=None, max_length=120)
    monthly_limit: Decimal | None = Field(default=None, ge=0)
    start_date: date
    next_renewal_date: date | None = None
    is_active: bool = True
    notes: str | None = Field(default=None, max_length=4000)


class SubscriptionResponse(BaseModel):
    """Single subscription resource."""

    id: UUID
    user_id: UUID
    name: str
    amount: Decimal
    currency: str
    billing_cycle: BillingCycleSchema
    category: str | None
    monthly_limit: Decimal | None
    start_date: date
    next_renewal_date: date | None
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
    monthly_equivalent: Decimal
