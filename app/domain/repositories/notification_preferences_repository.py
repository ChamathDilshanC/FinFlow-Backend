"""Notification preferences persistence port."""

from typing import Protocol
from uuid import UUID

from app.domain.entities.notification_preferences import NotificationPreferences


class NotificationPreferencesRepository(Protocol):
    """Single preferences row per user."""

    async def get_for_user(self, user_id: UUID) -> NotificationPreferences | None:
        """Return preferences or ``None`` if not initialized."""

    async def upsert(self, prefs: NotificationPreferences) -> NotificationPreferences:
        """Insert or update by ``user_id``."""
