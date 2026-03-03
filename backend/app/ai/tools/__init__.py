"""Tool definitions and default registry setup."""

from app.ai.tools.lead_tools import (
    handle_confirm_interest,
    handle_move_to_matching,
    handle_set_location,
    handle_start_collection,
    handle_start_negotiation,
    handle_update_budget,
    handle_validate_budget,
)
from app.ai.tools.property_tools import handle_evaluate_budget, handle_get_matching_properties
from app.ai.tools.registry import ToolRegistry
from app.ai.tools.schema import ToolDefinition


def build_default_registry() -> ToolRegistry:
    """Create a fully-wired tool registry with all known tools."""
    registry = ToolRegistry()

    registry.register(
        ToolDefinition(
            name="start_collection",
            description="Start collecting buyer requirements.",
            parameters={"type": "object", "properties": {}, "required": []},
        ),
        handle_start_collection,
    )

    registry.register(
        ToolDefinition(
            name="update_budget",
            description="Update the buyer's budget range.",
            parameters={
                "type": "object",
                "properties": {
                    "budget_min": {"type": "number", "description": "Minimum budget"},
                    "budget_max": {"type": "number", "description": "Maximum budget"},
                },
                "required": ["budget_min", "budget_max"],
            },
        ),
        handle_update_budget,
    )

    registry.register(
        ToolDefinition(
            name="set_location",
            description="Set the buyer's preferred location.",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Preferred city or area"},
                },
                "required": ["location"],
            },
        ),
        handle_set_location,
    )

    registry.register(
        ToolDefinition(
            name="validate_budget",
            description="Transition lead to budget validation state.",
            parameters={"type": "object", "properties": {}, "required": []},
        ),
        handle_validate_budget,
    )

    registry.register(
        ToolDefinition(
            name="move_to_matching",
            description="Transition lead to property matching state.",
            parameters={"type": "object", "properties": {}, "required": []},
        ),
        handle_move_to_matching,
    )

    registry.register(
        ToolDefinition(
            name="get_matching_properties",
            description="Retrieve properties matching the buyer's requirements.",
            parameters={"type": "object", "properties": {}, "required": []},
        ),
        handle_get_matching_properties,
    )

    registry.register(
        ToolDefinition(
            name="start_negotiation",
            description="Begin the negotiation phase with the buyer.",
            parameters={"type": "object", "properties": {}, "required": []},
        ),
        handle_start_negotiation,
    )

    registry.register(
        ToolDefinition(
            name="evaluate_budget",
            description="Evaluate buyer's budget against a specific property price.",
            parameters={
                "type": "object",
                "properties": {
                    "property_price": {"type": "number", "description": "Price of the property"},
                },
                "required": ["property_price"],
            },
        ),
        handle_evaluate_budget,
    )

    registry.register(
        ToolDefinition(
            name="confirm_interest",
            description="Confirm whether the buyer is interested or not.",
            parameters={
                "type": "object",
                "properties": {
                    "interested": {"type": "boolean", "description": "True if buyer is interested"},
                },
                "required": ["interested"],
            },
        ),
        handle_confirm_interest,
    )

    return registry
