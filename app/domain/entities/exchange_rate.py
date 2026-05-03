"""Cached FX rate for multi-currency reporting."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class ExchangeRate:
    """Quote per one unit of base currency."""

    id: UUID
    rate_date: date
    base_currency: str
    quote_currency: str
    rate: Decimal
    created_at: datetime
