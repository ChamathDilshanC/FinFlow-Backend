"""Notification preferences orchestration."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.entities.notification_preferences import NotificationPreferences
from app.domain.repositories.notification_preferences_repository import NotificationPreferencesRepository


def _default_preferences(user_id: UUID) -> NotificationPreferences:
    """Seed row when the user opens notification settings for the first time."""
    now = datetime.now(tz=UTC)
    return NotificationPreferences(
        id=uuid4(),
        user_id=user_id,
        email_enabled=True,
        days_before_renewal=7,
        timezone="UTC",
        created_at=now,
        updated_at=now,
    )


class NotificationService:
    """Load or create renewal-notification settings."""

    def __init__(self, preferences_repository: NotificationPreferencesRepository) -> None:
        self._repo = preferences_repository

    async def get_or_create(self, user_id: UUID) -> NotificationPreferences:
        existing = await self._repo.get_for_user(user_id)
        if existing is not None:
            return existing
        return await self._repo.upsert(_default_preferences(user_id))

    async def update_preferences(
        self,
        user_id: UUID,
        *,
        email_enabled: bool,
        days_before_renewal: int,
        timezone: str,
    ) -> NotificationPreferences:
        base = await self.get_or_create(user_id)
        now = datetime.now(tz=UTC)
        updated = NotificationPreferences(
            id=base.id,
            user_id=base.user_id,
            email_enabled=email_enabled,
            days_before_renewal=days_before_renewal,
            timezone=timezone.strip() or "UTC",
            created_at=base.created_at,
            updated_at=now,
        )
        return await self._repo.upsert(updated)
