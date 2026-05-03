"""Transaction (expense) API schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    category_id: UUID | None = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, default="USD")
    occurred_at: datetime
    merchant: str | None = Field(None, max_length=200)
    notes: str | None = Field(None, max_length=4000)


class TransactionUpdate(BaseModel):
    category_id: UUID | None = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    occurred_at: datetime
    merchant: str | None = Field(None, max_length=200)
    notes: str | None = Field(None, max_length=4000)


class TransactionResponse(BaseModel):
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
