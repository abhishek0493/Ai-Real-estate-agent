"""Tool validator — validates tool calls before execution."""

from __future__ import annotations

from typing import Any

from app.ai.tools.registry import ToolRegistry
from app.ai.tools.schema import ToolCall
from app.domain.entities.lead import LeadStatus


class ToolValidationError(Exception):
    """Raised when a tool call fails validation."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# Tools that are allowed in each lead state.
# If a state is absent, no tools at all are allowed in that state.
_STATE_TOOL_ALLOWLIST: dict[LeadStatus, frozenset[str]] = {
    LeadStatus.INIT: frozenset({"start_collection"}),
    LeadStatus.COLLECTING_REQUIREMENTS: frozenset({"update_budget", "set_location", "validate_budget"}),
    LeadStatus.VALIDATING_BUDGET: frozenset({"move_to_matching"}),
    LeadStatus.MATCHING_PROPERTIES: frozenset({"get_matching_properties", "start_negotiation"}),
    LeadStatus.NEGOTIATING: frozenset({"evaluate_budget", "confirm_interest"}),
    LeadStatus.CONFIRMING: frozenset({"confirm_interest"}),
}


class ToolValidator:
    """Validates that a tool call is safe to execute.

    Checks:
    1. Tool exists in the registry.
    2. Required parameters are present.
    3. Tool is allowed in the current lead state.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def validate(
        self,
        tool_call: ToolCall,
        current_state: LeadStatus,
    ) -> None:
        """Raise ``ToolValidationError`` if the call is invalid."""
        # 1. Tool must exist
        entry = self._registry.get_tool(tool_call.name)
        if entry is None:
            raise ToolValidationError(f"Unknown tool: {tool_call.name}")

        definition, _ = entry

        # 2. Check required parameters from JSON schema
        required = definition.parameters.get("required", [])
        for param in required:
            if param not in tool_call.arguments:
                raise ToolValidationError(
                    f"Missing required parameter '{param}' for tool '{tool_call.name}'"
                )

        # 3. Tool must be allowed in current state
        allowed_tools = _STATE_TOOL_ALLOWLIST.get(current_state, frozenset())
        if tool_call.name not in allowed_tools:
            raise ToolValidationError(
                f"Tool '{tool_call.name}' is not allowed in state {current_state.value}"
            )
