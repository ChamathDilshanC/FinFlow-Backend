"""Authentication-related DTOs."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """User registration payload."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_bytes_within_bcrypt_limit(cls, v: str) -> str:
        """Bcrypt hashes at most 72 UTF-8 bytes."""
        if len(v.encode("utf-8")) > 72:
            msg = "Password must be at most 72 bytes (UTF-8)"
            raise ValueError(msg)
        return v


class LoginRequest(BaseModel):
    """Password login payload."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def password_bytes_within_bcrypt_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            msg = "Password must be at most 72 bytes (UTF-8)"
            raise ValueError(msg)
        return v


class TokenResponse(BaseModel):
    """
    OAuth2-compatible token response (access-only MVP).

    ``refresh_token`` is present for forward compatibility; it is ``null`` until
    refresh issuance is implemented.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    refresh_token: str | None = None


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
