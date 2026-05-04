"""Authentication-related DTOs."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


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


class EmailPasswordRequest(BaseModel):
    """Email + password for Supabase email provider (sign up / sign in)."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=256)


class AuthSessionResponse(BaseModel):
    """
    Session returned after register or login.

    When Supabase has **Confirm email** enabled, sign-up may return no tokens until the user verifies;
    ``requires_email_confirmation`` is True in that case.
    """

    access_token: str | None = None
    refresh_token: str | None = None
    expires_in: int | None = None
    token_type: str = "bearer"
    requires_email_confirmation: bool = False
    user_id: UUID
    email: str
