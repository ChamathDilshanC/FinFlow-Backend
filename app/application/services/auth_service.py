"""
Authentication: sync Supabase-authenticated users into the app ``users`` table
and profile reads/updates.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.domain.entities.user import User
from app.domain.exceptions import IdentityEmailConflictError, UserNotFoundError
from app.domain.repositories.user_repository import UserRepository


@dataclass(slots=True)
class AuthService:
    """
    Map Supabase identities to local user rows and maintain profile fields.

    Args:
        user_repository: User persistence port.
    """

    _users: UserRepository

    async def sync_supabase_user(self, supabase_sub: UUID, email: str) -> User:
        """
        Ensure a ``users`` row exists for the Supabase ``auth.users`` id (JWT ``sub``).

        Uses ``users.id == sub`` so foreign keys across the app stay aligned.

        Raises:
            IdentityEmailConflictError: When ``email`` is taken by another ``id``.
        """
        normalized = email.strip().lower()
        existing = await self._users.get_by_id(supabase_sub)
        now = datetime.now(tz=UTC)

        if existing:
            if existing.email != normalized:
                updated = User(
                    id=existing.id,
                    email=normalized,
                    hashed_password=existing.hashed_password,
                    monthly_budget=existing.monthly_budget,
                    default_currency=existing.default_currency,
                    created_at=existing.created_at,
                    updated_at=now,
                )
                return await self._users.update(updated)
            return existing

        other = await self._users.get_by_email(normalized)
        if other is not None and other.id != supabase_sub:
            raise IdentityEmailConflictError()

        user = User(
            id=supabase_sub,
            email=normalized,
            hashed_password=None,
            monthly_budget=None,
            default_currency=None,
            created_at=now,
            updated_at=now,
        )
        return await self._users.create(user)

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
        """Update the user's global monthly budget cap used by dashboard analytics."""
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
