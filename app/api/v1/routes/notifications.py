"""Notification preferences (renewal reminders)."""

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import CurrentUserId, get_notification_service
from app.api.v1.schemas.notifications import NotificationPreferencesResponse, NotificationPreferencesUpdate
from app.application.services.notification_service import NotificationService
router = APIRouter()


def _resp(p) -> NotificationPreferencesResponse:
    return NotificationPreferencesResponse(
        id=p.id,
        user_id=p.user_id,
        email_enabled=p.email_enabled,
        days_before_renewal=p.days_before_renewal,
        timezone=p.timezone,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(
    user_id: CurrentUserId,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationPreferencesResponse:
    prefs = await service.get_or_create(user_id)
    return _resp(prefs)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    body: NotificationPreferencesUpdate,
    user_id: CurrentUserId,
    service: NotificationService = Depends(get_notification_service),
) -> NotificationPreferencesResponse:
    prefs = await service.update_preferences(
        user_id,
        email_enabled=body.email_enabled,
        days_before_renewal=body.days_before_renewal,
        timezone=body.timezone,
    )
    return _resp(prefs)
