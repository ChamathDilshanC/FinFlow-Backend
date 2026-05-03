"""Per-user notification settings for renewals and alerts."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class NotificationPreferences:
    """
    One row per user: email toggles and lead time before renewals.
    """

    id: UUID
    user_id: UUID
    email_enabled: bool
    days_before_renewal: int
    timezone: str
    created_at: datetime
    updated_at: datetime
