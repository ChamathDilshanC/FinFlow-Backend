"""Budget allocation API schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class BudgetAllocationCreate(BaseModel):
    category_id: UUID
    budget_month: date = Field(description="Any date in the target month (normalized to first day).")
    limit_amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)


class BudgetAllocationUpdate(BaseModel):
    category_id: UUID
    budget_month: date
    limit_amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)


class BudgetAllocationResponse(BaseModel):
    id: UUID
    user_id: UUID
    category_id: UUID
    budget_month: date
    limit_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime
