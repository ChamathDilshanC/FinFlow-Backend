"""ORM table mappings (import side-effect: register metadata for Alembic)."""

from app.infrastructure.database.models.budget_allocation import BudgetAllocationModel
from app.infrastructure.database.models.category import CategoryModel
from app.infrastructure.database.models.exchange_rate import ExchangeRateModel
from app.infrastructure.database.models.notification_preference import NotificationPreferenceModel
from app.infrastructure.database.models.payment import PaymentModel
from app.infrastructure.database.models.subscription import SubscriptionModel
from app.infrastructure.database.models.transaction import TransactionModel
from app.infrastructure.database.models.user import UserModel

__all__ = [
    "BudgetAllocationModel",
    "CategoryModel",
    "ExchangeRateModel",
    "NotificationPreferenceModel",
    "PaymentModel",
    "SubscriptionModel",
    "TransactionModel",
    "UserModel",
]
