"""
User repository port.

Keeps persistence concerns out of application services; implementations live in
``app.infrastructure.repositories``.
"""

from typing import Protocol
from uuid import UUID

from app.domain.entities.user import User


class UserRepository(Protocol):
    """
    Contract for loading and persisting users.

    Implementations must be async and transaction-aware where applicable.
    """

    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Fetch a user by primary key.

        Args:
            user_id: Identifier of the user row.

        Returns:
            Domain entity if found; otherwise ``None``.
        """

    async def get_by_email(self, email: str) -> User | None:
        """
        Fetch a user by unique email (case-insensitive match recommended).

        Args:
            email: Login email.

        Returns:
            Domain entity if found; otherwise ``None``.
        """

    async def create(self, user: User) -> User:
        """
        Insert a new user row.

        Args:
            user: Entity including generated ``id`` or DB-assigned key policy.

        Returns:
            Persisted user (same identifiers as stored).
        """

    async def update(self, user: User) -> User:
        """
        Persist updates to an existing user.

        Args:
            user: Entity with modified fields.

        Returns:
            Updated entity snapshot.
        """
