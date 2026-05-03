"""Dashboard analytics DTOs."""

from decimal import Decimal

from pydantic import BaseModel


class CategorySpendResponse(BaseModel):
    """Category rollup row."""

    category: str
    monthly_equivalent_total: Decimal


class DashboardSummaryResponse(BaseModel):
    """Aggregated snapshot for clients."""

    active_subscription_count: int
    monthly_equivalent_total: Decimal
    monthly_budget: Decimal | None
    remaining_budget: Decimal | None
    over_budget: bool
    limit_warnings: list[str]
    spend_by_category: list[CategorySpendResponse]
    expense_total_mtd: Decimal
    payment_records_total: int
    default_currency: str | None
