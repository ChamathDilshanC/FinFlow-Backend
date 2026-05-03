"""
User aggregate root for authentication and budget tracking.

Amounts use ``Decimal`` to avoid floating-point drift in financial calculations.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class User:
    """
    Represents an authenticated account.

    Attributes:
        id: Stable primary identifier.
        email: Unique login identifier (lowercase normalized in services).
        hashed_password: Bcrypt hash for password users; ``None`` for OAuth-only (Supabase).
        monthly_budget: Optional global monthly spending cap for dashboard alerts.
        created_at: Record creation timestamp (UTC).
        updated_at: Last mutation timestamp (UTC).
    """

    id: UUID
    email: str
    hashed_password: str | None
    monthly_budget: Decimal | None
    default_currency: str | None
    created_at: datetime
    updated_at: datetime
