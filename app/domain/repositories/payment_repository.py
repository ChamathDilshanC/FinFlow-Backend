"""Payment log persistence port."""

from typing import Protocol
from uuid import UUID

from app.domain.entities.payment import Payment


class PaymentRepository(Protocol):
    """Recorded payments."""

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        skip: int,
        limit: int,
        subscription_id: UUID | None,
    ) -> tuple[list[Payment], int]:
        """Paginated payments."""

    async def get_for_user(self, user_id: UUID, payment_id: UUID) -> Payment | None:
        """Load payment owned by user."""

    async def count_for_user(self, user_id: UUID) -> int:
        """Total payments recorded."""

    async def create(self, payment: Payment) -> Payment:
        """Insert payment."""

    async def update(self, payment: Payment) -> Payment:
        """Update payment."""

    async def delete(self, user_id: UUID, payment_id: UUID) -> bool:
        """Delete owned payment."""
