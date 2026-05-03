"""
Aggregated API v1 router mounted under ``/api/v1`` in :mod:`app.main`.
"""

from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    budgets,
    categories,
    dashboard,
    exchange_rates,
    notifications,
    payments,
    subscriptions,
    transactions,
)

api_v1_router = APIRouter()
api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(
    subscriptions.router,
    prefix="/subscriptions",
    tags=["subscriptions"],
)
api_v1_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"],
)
api_v1_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_v1_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_v1_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_v1_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_v1_router.include_router(budgets.router, prefix="/budgets", tags=["budgets"])
api_v1_router.include_router(exchange_rates.router, prefix="/exchange-rates", tags=["exchange-rates"])
