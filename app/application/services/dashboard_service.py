"""
Dashboard analytics aggregating normalized spend, budgets, expenses, and payments.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from app.application.finance import monthly_equivalent, sum_monthly_equivalent
from app.domain.entities.subscription import Subscription
from app.domain.exceptions import UserNotFoundError
from app.domain.repositories.payment_repository import PaymentRepository
from app.domain.repositories.subscription_repository import SubscriptionRepository
from app.domain.repositories.transaction_repository import TransactionRepository
from app.domain.repositories.user_repository import UserRepository


@dataclass(slots=True)
class CategorySpend:
    """Per-category monthly-equivalent rollup for subscriptions."""

    category: str
    monthly_equivalent_total: Decimal


@dataclass(slots=True)
class DashboardSummary:
    """
    High-level finance snapshot for the authenticated user.

    Includes subscription modelling, optional expense MTD totals (same-currency sum),
    payment record counts, and profile currency hint.
    """

    active_subscription_count: int
    monthly_equivalent_total: Decimal
    monthly_budget: Decimal | None
    remaining_budget: Decimal | None
    over_budget: bool
    limit_warnings: list[str]
    spend_by_category: list[CategorySpend]
    expense_total_mtd: Decimal
    payment_records_total: int
    default_currency: str | None


class DashboardService:
    """
    Compose dashboard analytics from multiple repositories.

    Args:
        user_repository: User profile and budget cap.
        subscription_repository: Active subscriptions for rollup.
        transaction_repository: Expense ledger (month-to-date sum).
        payment_repository: Payment log counts.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        subscription_repository: SubscriptionRepository,
        transaction_repository: TransactionRepository,
        payment_repository: PaymentRepository,
    ) -> None:
        self._users = user_repository
        self._subs = subscription_repository
        self._tx = transaction_repository
        self._pay = payment_repository

    async def get_summary(self, user_id: UUID) -> DashboardSummary:
        """
        Build analytics for ``/dashboard/summary``.

        Raises:
            UserNotFoundError: Propagated when the user row is missing.
        """
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()

        active = await self._subs.list_active_for_user(user_id)
        tuples = [(s.amount, s.billing_cycle) for s in active]
        total = sum_monthly_equivalent(tuples)

        budget = user.monthly_budget
        remaining: Decimal | None = None
        over = False
        if budget is not None:
            remaining = budget - total
            over = total > budget

        warnings = self._limit_warnings(active)
        by_cat = self._category_breakdown(active)

        now = datetime.now(tz=UTC)
        month_start = datetime(now.year, now.month, 1, tzinfo=UTC)
        if now.month == 12:
            next_month_start = datetime(now.year + 1, 1, 1, tzinfo=UTC)
        else:
            next_month_start = datetime(now.year, now.month + 1, 1, tzinfo=UTC)
        month_end_inclusive = next_month_start - timedelta(microseconds=1)

        expense_mtd_raw = await self._tx.sum_amount_for_user_period(
            user_id,
            from_occurred=month_start,
            to_occurred=month_end_inclusive,
        )
        expense_total_mtd = Decimal(str(expense_mtd_raw))

        payment_records_total = await self._pay.count_for_user(user_id)

        return DashboardSummary(
            active_subscription_count=len(active),
            monthly_equivalent_total=total,
            monthly_budget=budget,
            remaining_budget=remaining,
            over_budget=over,
            limit_warnings=warnings,
            spend_by_category=by_cat,
            expense_total_mtd=expense_total_mtd,
            payment_records_total=payment_records_total,
            default_currency=user.default_currency,
        )

    def _limit_warnings(self, subscriptions: list[Subscription]) -> list[str]:
        """Identify subscriptions breaching their optional per-row monthly limits."""
        messages: list[str] = []
        for s in subscriptions:
            if s.monthly_limit is None:
                continue
            me = monthly_equivalent(s.amount, s.billing_cycle)
            if me > s.monthly_limit:
                messages.append(
                    f"{s.name}: monthly-equivalent {me} exceeds monthly_limit {s.monthly_limit}",
                )
        return messages

    def _category_breakdown(self, subscriptions: list[Subscription]) -> list[CategorySpend]:
        """Aggregate monthly-equivalent totals per subscription category label."""
        totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for s in subscriptions:
            key = s.category.strip() if s.category else "uncategorized"
            totals[key] += monthly_equivalent(s.amount, s.billing_cycle)
        return [
            CategorySpend(category=k, monthly_equivalent_total=v)
            for k, v in sorted(totals.items(), key=lambda kv: kv[0])
        ]
