"""
FastAPI dependencies wiring repositories, services, and authentication.

``get_current_user_id`` validates JWT bearer tokens and returns the subject user id.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

import jwt

from app.application.services.auth_service import AuthService
from app.application.services.budget_allocation_service import BudgetAllocationService
from app.application.services.category_service import CategoryService
from app.application.services.dashboard_service import DashboardService
from app.application.services.exchange_rate_service import ExchangeRateService
from app.application.services.notification_service import NotificationService
from app.application.services.payment_record_service import PaymentRecordService
from app.application.services.subscription_service import SubscriptionService
from app.application.services.transaction_service import TransactionService
from app.config import Settings, get_settings
from app.core.exceptions import AppHTTPException
from app.core.supabase_jwt import parse_supabase_user_identity, verify_supabase_access_token
from app.domain.exceptions import IdentityEmailConflictError
from app.infrastructure.database.session import get_db_session
from app.infrastructure.repositories.budget_allocation_repository import SqlAlchemyBudgetAllocationRepository
from app.infrastructure.repositories.category_repository import SqlAlchemyCategoryRepository
from app.infrastructure.repositories.exchange_rate_repository import SqlAlchemyExchangeRateRepository
from app.infrastructure.repositories.notification_preferences_repository import SqlAlchemyNotificationPreferencesRepository
from app.infrastructure.repositories.payment_repository import SqlAlchemyPaymentRepository
from app.infrastructure.repositories.subscription_repository import SqlAlchemySubscriptionRepository
from app.infrastructure.repositories.transaction_repository import SqlAlchemyTransactionRepository
from app.infrastructure.repositories.user_repository import SqlAlchemyUserRepository

_http_bearer = HTTPBearer(auto_error=False)


async def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuthService:
    """Resolve an :class:`AuthService` bound to the request session."""
    users = SqlAlchemyUserRepository(session)
    return AuthService(users)


async def get_subscription_service(
    session: AsyncSession = Depends(get_db_session),
) -> SubscriptionService:
    """Resolve a :class:`SubscriptionService` with SQLAlchemy repositories."""
    repo = SqlAlchemySubscriptionRepository(session)
    return SubscriptionService(repo)


async def get_dashboard_service(
    session: AsyncSession = Depends(get_db_session),
) -> DashboardService:
    """Resolve dashboard analytics with shared session repositories."""
    return DashboardService(
        SqlAlchemyUserRepository(session),
        SqlAlchemySubscriptionRepository(session),
        SqlAlchemyTransactionRepository(session),
        SqlAlchemyPaymentRepository(session),
    )


async def get_category_service(
    session: AsyncSession = Depends(get_db_session),
) -> CategoryService:
    """Category CRUD service."""
    return CategoryService(SqlAlchemyCategoryRepository(session))


async def get_transaction_service(
    session: AsyncSession = Depends(get_db_session),
) -> TransactionService:
    """Expense transaction service."""
    return TransactionService(
        SqlAlchemyTransactionRepository(session),
        SqlAlchemyCategoryRepository(session),
    )


async def get_payment_record_service(
    session: AsyncSession = Depends(get_db_session),
) -> PaymentRecordService:
    """Payment log service."""
    return PaymentRecordService(
        SqlAlchemyPaymentRepository(session),
        SqlAlchemySubscriptionRepository(session),
    )


async def get_notification_service(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationService:
    """Notification preferences service."""
    return NotificationService(SqlAlchemyNotificationPreferencesRepository(session))


async def get_budget_allocation_service(
    session: AsyncSession = Depends(get_db_session),
) -> BudgetAllocationService:
    """Category budget service."""
    return BudgetAllocationService(
        SqlAlchemyBudgetAllocationRepository(session),
        SqlAlchemyCategoryRepository(session),
    )


async def get_exchange_rate_service(
    session: AsyncSession = Depends(get_db_session),
) -> ExchangeRateService:
    """FX cache service."""
    return ExchangeRateService(SqlAlchemyExchangeRateRepository(session))


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> UUID:
    """
    Validate ``Authorization: Bearer <Supabase access token>``, upsert local user, return id.

    The JWT ``sub`` must equal ``users.id`` (Supabase ``auth.users`` UUID).

    Raises:
        AppHTTPException: 401 when the token is missing or invalid.
        AppHTTPException: 409 when email conflicts with another account.
    """
    if credentials is None or not credentials.credentials:
        raise AppHTTPException(
            detail="Not authenticated",
            code="NOT_AUTHENTICATED",
            status_code=401,
        )
    try:
        payload = verify_supabase_access_token(credentials.credentials, settings)
        supabase_sub, email = parse_supabase_user_identity(payload)
        user = await auth_service.sync_supabase_user(supabase_sub, email)
        return user.id
    except AppHTTPException:
        raise
    except jwt.PyJWTError as exc:
        raise AppHTTPException(
            detail="Could not validate credentials",
            code="INVALID_TOKEN",
            status_code=401,
        ) from exc
    except ValueError as exc:
        raise AppHTTPException(
            detail=str(exc),
            code="INVALID_TOKEN",
            status_code=401,
        ) from exc
    except IdentityEmailConflictError as exc:
        raise AppHTTPException(
            detail=exc.message,
            code=exc.code,
            status_code=409,
        ) from exc


CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]

