"""Payment log API schemas."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentStatusSchema(str, Enum):
    paid = "paid"
    pending = "pending"
    failed = "failed"
    cancelled = "cancelled"


class PaymentSourceSchema(str, Enum):
    manual = "manual"
    IMPORT = "import"
    system = "system"


class PaymentCreate(BaseModel):
    subscription_id: UUID | None = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    paid_at: datetime
    period_start: date | None = None
    period_end: date | None = None
    status: PaymentStatusSchema = PaymentStatusSchema.paid
    source: PaymentSourceSchema = PaymentSourceSchema.manual
    notes: str | None = Field(None, max_length=4000)


class PaymentUpdate(BaseModel):
    subscription_id: UUID | None = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    paid_at: datetime
    period_start: date | None = None
    period_end: date | None = None
    status: PaymentStatusSchema
    source: PaymentSourceSchema
    notes: str | None = Field(None, max_length=4000)


class PaymentResponse(BaseModel):
    id: UUID
    user_id: UUID
    subscription_id: UUID | None
    amount: Decimal
    currency: str
    paid_at: datetime
    period_start: date | None
    period_end: date | None
    status: PaymentStatusSchema
    source: PaymentSourceSchema
    notes: str | None
    created_at: datetime
    updated_at: datetime
