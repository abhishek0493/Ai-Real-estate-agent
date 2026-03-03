"""Property-related tool handlers."""

from __future__ import annotations

from typing import Any

from app.domain.entities.lead import Lead
from app.domain.negotiation.engine import evaluate_budget


async def handle_get_matching_properties(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """Stub — in production, queries the property repository.

    Returns a placeholder list so the orchestrator pipeline is complete.
    """
    return {
        "action": "get_matching_properties",
        "properties": [],
        "note": "Repository not yet wired — stub response",
    }


async def handle_evaluate_budget(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """Evaluate a lead's budget against a property price using the domain engine."""
    property_price = float(kwargs["property_price"])

    if lead.budget_min is None or lead.budget_max is None:
        return {"action": "evaluate_budget", "error": "Budget not set on lead"}

    result = evaluate_budget(lead.budget_min, lead.budget_max, property_price)
    return {
        "action": "evaluate_budget",
        "result": result.value,
        "property_price": property_price,
        "budget_min": lead.budget_min,
        "budget_max": lead.budget_max,
    }
