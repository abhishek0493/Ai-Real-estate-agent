"""Budget negotiation engine — deterministic, no AI."""

from __future__ import annotations

from enum import Enum

from app.domain.exceptions import NegotiationError


class NegotiationResult(str, Enum):
    """Possible outcomes of a budget-vs-price evaluation."""

    ACCEPTABLE = "ACCEPTABLE"
    SOFT_NEGOTIATE = "SOFT_NEGOTIATE"
    SUGGEST_ALTERNATIVE = "SUGGEST_ALTERNATIVE"
    OUT_OF_RANGE = "OUT_OF_RANGE"


def evaluate_budget(
    user_budget_min: float,
    user_budget_max: float,
    property_price: float,
) -> NegotiationResult:
    """Evaluate a buyer's budget range against a property price.

    Rules (applied in order):
    1. Price within budget range           → ACCEPTABLE
    2. Price exceeds budget_max by ≤ 5%    → SOFT_NEGOTIATE
    3. Price exceeds budget_max by ≤ 15%   → SUGGEST_ALTERNATIVE
    4. Otherwise                           → OUT_OF_RANGE
    """
    if property_price <= 0:
        raise NegotiationError("property_price must be positive")
    if user_budget_min < 0 or user_budget_max < 0:
        raise NegotiationError("Budget values must be non-negative")
    if user_budget_min > user_budget_max:
        raise NegotiationError("budget_min cannot exceed budget_max")

    # Within range
    if user_budget_min <= property_price <= user_budget_max:
        return NegotiationResult.ACCEPTABLE

    # Price above budget — how far?
    if property_price > user_budget_max:
        overshoot_pct = ((property_price - user_budget_max) / user_budget_max) * 100

        if overshoot_pct <= 5:
            return NegotiationResult.SOFT_NEGOTIATE
        if overshoot_pct <= 15:
            return NegotiationResult.SUGGEST_ALTERNATIVE
        return NegotiationResult.OUT_OF_RANGE

    # Price *below* budget — always acceptable
    return NegotiationResult.ACCEPTABLE
