"""Domain-level exceptions (business rule violations)."""


class DomainError(Exception):
    """Base class for predictable domain failures."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class EmailAlreadyRegisteredError(DomainError):
    """Raised when registration targets an email that already exists."""

    def __init__(self, message: str = "Email is already registered") -> None:
        super().__init__(message, code="EMAIL_ALREADY_REGISTERED")


class InvalidCredentialsError(DomainError):
    """Raised when login credentials cannot be verified."""

    def __init__(self, message: str = "Invalid email or password") -> None:
        super().__init__(message, code="INVALID_CREDENTIALS")


class SubscriptionNotFoundError(DomainError):
    """Raised when a subscription does not exist or is not owned by the user."""

    def __init__(self, message: str = "Subscription not found") -> None:
        super().__init__(message, code="SUBSCRIPTION_NOT_FOUND")


class UserNotFoundError(DomainError):
    """Raised when a user cannot be resolved."""

    def __init__(self, message: str = "User not found") -> None:
        super().__init__(message, code="USER_NOT_FOUND")


class CategoryNotFoundError(DomainError):
    """Raised when a category is missing or not owned."""

    def __init__(self, message: str = "Category not found") -> None:
        super().__init__(message, code="CATEGORY_NOT_FOUND")


class TransactionNotFoundError(DomainError):
    """Raised when a transaction row is missing."""

    def __init__(self, message: str = "Transaction not found") -> None:
        super().__init__(message, code="TRANSACTION_NOT_FOUND")


class PaymentNotFoundError(DomainError):
    """Raised when a payment row is missing."""

    def __init__(self, message: str = "Payment not found") -> None:
        super().__init__(message, code="PAYMENT_NOT_FOUND")


class BudgetNotFoundError(DomainError):
    """Raised when a budget allocation row is missing."""

    def __init__(self, message: str = "Budget allocation not found") -> None:
        super().__init__(message, code="BUDGET_NOT_FOUND")


class ExchangeRateNotFoundError(DomainError):
    """Raised when an FX row is missing."""

    def __init__(self, message: str = "Exchange rate not found") -> None:
        super().__init__(message, code="EXCHANGE_RATE_NOT_FOUND")
