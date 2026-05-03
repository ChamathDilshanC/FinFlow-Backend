"""
Pure financial normalization helpers (no I/O).

Monthly equivalents power budget comparisons independent of billing cadence.
"""

from decimal import Decimal

from app.domain.entities.subscription import BillingCycle


def monthly_equivalent(amount: Decimal, billing_cycle: BillingCycle) -> Decimal:
    """
    Convert a per-cycle charge into an approximate monthly amount.

    Args:
        amount: Price charged each billing cycle.
        billing_cycle: Cadence for ``amount``.

    Returns:
        Decimal monthly-equivalent (quantize at API boundary if needed).
    """
    if billing_cycle == BillingCycle.WEEKLY:
        return amount * Decimal(52) / Decimal(12)
    if billing_cycle == BillingCycle.MONTHLY:
        return amount
    if billing_cycle == BillingCycle.QUARTERLY:
        return amount / Decimal(3)
    if billing_cycle == BillingCycle.YEARLY:
        return amount / Decimal(12)
    msg = f"Unsupported billing cycle: {billing_cycle}"
    raise ValueError(msg)


def sum_monthly_equivalent(subscriptions: list[tuple[Decimal, BillingCycle]]) -> Decimal:
    """
    Sum monthly equivalents for many subscriptions.

    Args:
        subscriptions: Tuples of (amount, billing_cycle).

    Returns:
        Total monthly-equivalent spend.
    """
    total = Decimal("0.00")
    for amount, cycle in subscriptions:
        total += monthly_equivalent(amount, cycle)
    return total
