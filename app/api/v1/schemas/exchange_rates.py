"""Exchange rate cache API schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ExchangeRateResponse(BaseModel):
    id: UUID
    rate_date: date
    base_currency: str
    quote_currency: str
    rate: Decimal
    created_at: datetime


class ExchangeRateUpsert(BaseModel):
    rate_date: date
    base_currency: str = Field(min_length=3, max_length=3)
    quote_currency: str = Field(min_length=3, max_length=3)
    rate: Decimal = Field(gt=0)
