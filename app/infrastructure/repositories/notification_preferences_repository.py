"""SQLAlchemy notification preferences repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.notification_preferences import NotificationPreferences
from app.infrastructure.database.models.notification_preference import NotificationPreferenceModel


def _to_entity(row: NotificationPreferenceModel) -> NotificationPreferences:
    return NotificationPreferences(
        id=row.id,
        user_id=row.user_id,
        email_enabled=row.email_enabled,
        days_before_renewal=row.days_before_renewal,
        timezone=row.timezone,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyNotificationPreferencesRepository:
    """One preferences row per user."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_user(self, user_id: UUID) -> NotificationPreferences | None:
        stmt = select(NotificationPreferenceModel).where(
            NotificationPreferenceModel.user_id == user_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def upsert(self, prefs: NotificationPreferences) -> NotificationPreferences:
        existing = await self.get_for_user(prefs.user_id)
        if existing is None:
            model = NotificationPreferenceModel(
                id=prefs.id,
                user_id=prefs.user_id,
                email_enabled=prefs.email_enabled,
                days_before_renewal=prefs.days_before_renewal,
                timezone=prefs.timezone,
                created_at=prefs.created_at,
                updated_at=prefs.updated_at,
            )
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            return _to_entity(model)

        model = await self._session.get(NotificationPreferenceModel, existing.id)
        assert model is not None
        model.email_enabled = prefs.email_enabled
        model.days_before_renewal = prefs.days_before_renewal
        model.timezone = prefs.timezone
        model.updated_at = prefs.updated_at
        await self._session.flush()
        await self._session.refresh(model)
        return _to_entity(model)
