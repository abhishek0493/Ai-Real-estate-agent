"""Lead-related tool handlers — bridge between AI and domain services."""

from __future__ import annotations

from typing import Any

from app.domain.entities.lead import Lead
from app.domain.services.lead_flow_service import LeadFlowService

_flow = LeadFlowService()


async def handle_update_budget(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """Update the lead's budget range."""
    budget_min = float(kwargs["budget_min"])
    budget_max = float(kwargs["budget_max"])
    lead.update_budget(budget_min, budget_max)
    return {
        "action": "update_budget",
        "budget_min": budget_min,
        "budget_max": budget_max,
        "status": lead.status.value,
    }


async def handle_set_location(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """Set the lead's preferred location."""
    location = str(kwargs["location"])
    lead.preferred_location = location
    return {
        "action": "set_location",
        "preferred_location": location,
        "status": lead.status.value,
    }


async def handle_start_collection(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """INIT → COLLECTING_REQUIREMENTS."""
    prev, new = _flow.start_collection(lead)
    return {"action": "start_collection", "previous": prev.value, "current": new.value}


async def handle_validate_budget(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """COLLECTING_REQUIREMENTS → VALIDATING_BUDGET."""
    prev, new = _flow.validate_budget(lead)
    return {"action": "validate_budget", "previous": prev.value, "current": new.value}


async def handle_move_to_matching(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """VALIDATING_BUDGET → MATCHING_PROPERTIES."""
    prev, new = _flow.move_to_matching(lead)
    return {"action": "move_to_matching", "previous": prev.value, "current": new.value}


async def handle_start_negotiation(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """MATCHING_PROPERTIES → NEGOTIATING."""
    prev, new = _flow.start_negotiation(lead)
    return {"action": "start_negotiation", "previous": prev.value, "current": new.value}


async def handle_confirm_interest(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """NEGOTIATING → CONFIRMING → INTERESTED or NOT_INTERESTED."""
    interested = bool(kwargs.get("interested", True))
    prev, new = _flow.confirm_interest(lead, interested=interested)
    return {"action": "confirm_interest", "previous": prev.value, "current": new.value}


async def handle_update_preferences(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """Store buyer preferences (parking, near station, furnished, etc.)."""
    preferences = kwargs.get("preferences", [])
    if isinstance(preferences, str):
        preferences = [preferences]
    lead.preferences = list(set(lead.preferences + preferences))
    return {
        "action": "update_preferences",
        "preferences": lead.preferences,
        "status": lead.status.value,
    }


async def handle_set_bedrooms(lead: Lead, **kwargs: Any) -> dict[str, Any]:
    """Set the number of bedrooms the buyer is looking for."""
    bedrooms = int(kwargs["bedrooms"])
    lead.bedrooms = bedrooms
    return {
        "action": "set_bedrooms",
        "bedrooms": bedrooms,
        "status": lead.status.value,
    }
