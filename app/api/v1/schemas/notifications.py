"""Notification preferences API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationPreferencesResponse(BaseModel):
    id: UUID
    user_id: UUID
    email_enabled: bool
    days_before_renewal: int = Field(ge=0, le=90)
    timezone: str
    created_at: datetime
    updated_at: datetime


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: bool
    days_before_renewal: int = Field(ge=0, le=90)
    timezone: str = Field(min_length=1, max_length=64)
