"""Authentication-related DTOs."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    """Public user profile without secrets."""

    id: UUID
    email: str
    monthly_budget: Decimal | None
    default_currency: str | None
    created_at: datetime
    updated_at: datetime


class UserProfilePatch(BaseModel):
    """Optional profile fields; only send fields to change."""

    monthly_budget: Decimal | None = None
    default_currency: str | None = Field(
        default=None,
        max_length=3,
        description="ISO 4217 (e.g. USD, LKR). Null or empty clears.",
    )


class UpdateBudgetRequest(BaseModel):
    """Update the user's global monthly budget."""

    monthly_budget: Decimal | None = Field(
        default=None,
        description="Set to null to clear the budget cap.",
    )
