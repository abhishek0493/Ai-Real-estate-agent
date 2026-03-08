"""Property-related tool handlers."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.lead import Lead
from app.domain.negotiation.engine import evaluate_budget
from app.models.property import PropertyModel


def make_property_matcher(db: Session):
    """Factory that creates a DB-aware property matching handler."""

    async def handle_get_matching_properties(lead: Lead, **kwargs: Any) -> dict[str, Any]:
        """Query the property database for matches.

        Two-pass approach:
        1. Exact match: within budget
        2. If none found: widen to budget_max × 1.05 and tag as over_budget
        """
        base_stmt = select(PropertyModel).where(
            PropertyModel.tenant_id == lead.tenant_id,
            PropertyModel.available == True,
        )

        # Filter by location (case-insensitive partial match)
        if lead.preferred_location:
            base_stmt = base_stmt.where(
                PropertyModel.location.ilike(f"%{lead.preferred_location}%")
            )

        # Filter by bedrooms
        if lead.bedrooms is not None:
            base_stmt = base_stmt.where(PropertyModel.bedrooms == lead.bedrooms)

        # ── Pass 1: exact budget match ──
        exact_stmt = base_stmt
        if lead.budget_min is not None:
            exact_stmt = exact_stmt.where(PropertyModel.price >= lead.budget_min * 0.8)
        if lead.budget_max is not None:
            exact_stmt = exact_stmt.where(PropertyModel.price <= lead.budget_max)

        exact_stmt = exact_stmt.order_by(PropertyModel.price).limit(10)
        exact_results = list(db.scalars(exact_stmt).all())

        if exact_results:
            return _format_results(exact_results, within_budget=True)

        # ── Pass 2: 5% over budget fallback ──
        if lead.budget_max is not None:
            flex_stmt = base_stmt.where(
                PropertyModel.price <= lead.budget_max * 1.05,
            )
            if lead.budget_min is not None:
                flex_stmt = flex_stmt.where(PropertyModel.price >= lead.budget_min * 0.8)

            flex_stmt = flex_stmt.order_by(PropertyModel.price).limit(10)
            flex_results = list(db.scalars(flex_stmt).all())

            if flex_results:
                return _format_results(flex_results, within_budget=False)

        # ── No results at all ──
        return {
            "action": "get_matching_properties",
            "count": 0,
            "properties": [],
            "within_budget": True,
            "note": "No properties found matching the requirements.",
        }

    return handle_get_matching_properties


def _format_results(properties: list[PropertyModel], *, within_budget: bool) -> dict[str, Any]:
    """Format property results for the LLM."""
    result_list = [
        {
            "id": str(p.id),
            "location": p.location,
            "price": p.price,
            "bedrooms": p.bedrooms,
            "bathrooms": p.bathrooms,
            "square_feet": p.square_feet,
        }
        for p in properties
    ]

    return {
        "action": "get_matching_properties",
        "count": len(result_list),
        "properties": result_list,
        "within_budget": within_budget,
        "note": (
            "All properties are within the buyer's budget."
            if within_budget
            else "These properties are slightly above the buyer's stated budget (up to 5% over). "
                 "Inform the buyer that these options are available at a slightly higher price and ask if they'd consider them."
        ),
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
