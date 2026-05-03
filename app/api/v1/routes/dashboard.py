"""
Dashboard analytics (owner-scoped).
"""

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import CurrentUserId, get_dashboard_service
from app.api.v1.schemas.dashboard import CategorySpendResponse, DashboardSummaryResponse
from app.application.services.dashboard_service import DashboardService
from app.domain.exceptions import DomainError, UserNotFoundError
from app.core.exceptions import AppHTTPException

router = APIRouter()


def _map_domain(exc: DomainError) -> AppHTTPException:
    """Translate dashboard-level domain failures."""
    if isinstance(exc, UserNotFoundError):
        return AppHTTPException(detail=exc.message, code=exc.code, status_code=404)
    return AppHTTPException(detail=exc.message, code=exc.code, status_code=400)


@router.get("/summary", response_model=DashboardSummaryResponse)
async def dashboard_summary(
    user_id: CurrentUserId,
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummaryResponse:
    """
    Aggregated monthly-equivalent totals, budget headroom, and category splits.

    Requires authentication; results never leak cross-tenant data.
    """
    try:
        s = await service.get_summary(user_id)
    except DomainError as exc:
        raise _map_domain(exc) from exc

    return DashboardSummaryResponse(
        active_subscription_count=s.active_subscription_count,
        monthly_equivalent_total=s.monthly_equivalent_total,
        monthly_budget=s.monthly_budget,
        remaining_budget=s.remaining_budget,
        over_budget=s.over_budget,
        limit_warnings=s.limit_warnings,
        spend_by_category=[
            CategorySpendResponse(
                category=c.category,
                monthly_equivalent_total=c.monthly_equivalent_total,
            )
            for c in s.spend_by_category
        ],
        expense_total_mtd=s.expense_total_mtd,
        payment_records_total=s.payment_records_total,
        default_currency=s.default_currency,
    )
