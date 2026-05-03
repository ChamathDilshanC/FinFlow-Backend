"""
Authentication use cases: registration, login, and profile reads/updates.

Repositories encapsulate persistence; this module coordinates validation and tokens.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.config import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.entities.user import User
from app.domain.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError, UserNotFoundError
from app.domain.repositories.user_repository import UserRepository


@dataclass(slots=True)
class AuthTokens:
    """
    Token bundle returned by authentication flows.

    Attributes:
        access_token: Bearer token for API authorization (MVP).
        token_type: Always ``bearer`` for OAuth2-compatible clients.
        expires_in: Access token lifetime in seconds (informational).
        refresh_token: Reserved for refresh-token support (``None`` in MVP).
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    refresh_token: str | None = None


class AuthService:
    """
    Register and authenticate users; issue JWT access tokens.

    Args:
        user_repository: User persistence port.
        settings: JWT and password policy configuration.
    """

    def __init__(self, user_repository: UserRepository, settings: Settings) -> None:
        self._users = user_repository
        self._settings = settings

    async def register(self, email: str, password: str) -> AuthTokens:
        """
        Create a new user after uniqueness checks and return access token.

        Args:
            email: Login email (normalized to lowercase).
            password: Plaintext password to hash.

        Returns:
            :class:`AuthTokens` containing a new access JWT.

        Raises:
            EmailAlreadyRegisteredError: When the email is taken.
        """
        normalized = email.strip().lower()
        existing = await self._users.get_by_email(normalized)
        if existing:
            raise EmailAlreadyRegisteredError()

        now = datetime.now(tz=UTC)
        user = User(
            id=uuid4(),
            email=normalized,
            hashed_password=hash_password(password),
            monthly_budget=None,
            default_currency=None,
            created_at=now,
            updated_at=now,
        )
        created = await self._users.create(user)
        token = create_access_token(subject_user_id=created.id, settings=self._settings)
        return AuthTokens(
            access_token=token,
            expires_in=self._settings.access_token_expire_minutes * 60,
            refresh_token=None,
        )

    async def login(self, email: str, password: str) -> AuthTokens:
        """
        Verify credentials and mint an access token.

        Args:
            email: Login email.
            password: Plaintext password attempt.

        Returns:
            :class:`AuthTokens` for successful authentication.

        Raises:
            InvalidCredentialsError: When login fails.
        """
        normalized = email.strip().lower()
        user = await self._users.get_by_email(normalized)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        token = create_access_token(subject_user_id=user.id, settings=self._settings)
        return AuthTokens(
            access_token=token,
            expires_in=self._settings.access_token_expire_minutes * 60,
            refresh_token=None,
        )

    async def get_user(self, user_id: UUID) -> User:
        """
        Load a user by id for authenticated contexts.

        Raises:
            UserNotFoundError: When the user does not exist.
        """
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return user

    async def update_monthly_budget(self, user_id: UUID, monthly_budget: Decimal | None) -> User:
        """
        Update the user's global monthly budget cap used by dashboard analytics.

        Args:
            user_id: Authenticated user id.
            monthly_budget: New cap, or ``None`` to clear.

        Returns:
            Updated user entity.
        """
        user = await self.get_user(user_id)
        now = datetime.now(tz=UTC)
        updated = User(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            monthly_budget=monthly_budget,
            default_currency=user.default_currency,
            created_at=user.created_at,
            updated_at=now,
        )
        return await self._users.update(updated)

    async def patch_profile(self, user_id: UUID, updates: dict[str, Any]) -> User:
        """
        Partially update profile fields present in ``updates`` (from ``exclude_unset`` body).

        Supported keys: ``monthly_budget``, ``default_currency`` (ISO 4217 code or ``None``).
        """
        user = await self.get_user(user_id)
        now = datetime.now(tz=UTC)
        mb = user.monthly_budget
        if "monthly_budget" in updates:
            mb = updates["monthly_budget"]
        dc = user.default_currency
        if "default_currency" in updates:
            raw = updates["default_currency"]
            if raw is None or raw == "":
                dc = None
            else:
                dc = str(raw).strip().upper()[:3]
        updated = User(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            monthly_budget=mb,
            default_currency=dc,
            created_at=user.created_at,
            updated_at=now,
        )
        return await self._users.update(updated)
