"""Tool registry — maps tool names to definitions and handler functions."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.ai.tools.schema import ToolDefinition

# A handler receives (lead, **tool_arguments) and returns a result dict
ToolHandler = Callable[..., Awaitable[dict[str, Any]]]


class ToolRegistry:
    """Central registry of all tools available to the LLM.

    Each tool has a ``ToolDefinition`` (schema sent to the LLM) and a
    ``ToolHandler`` (backend function executed when the LLM calls it).
    """

    def __init__(self) -> None:
        self._tools: dict[str, tuple[ToolDefinition, ToolHandler]] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        """Register a tool definition + handler pair."""
        self._tools[definition.name] = (definition, handler)

    def get_tool(self, name: str) -> tuple[ToolDefinition, ToolHandler] | None:
        """Look up a tool by name.  Returns ``None`` if not found."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """Return all registered tool definitions."""
        return [defn for defn, _ in self._tools.values()]

    def list_openai_schemas(self) -> list[dict[str, Any]]:
        """Return all tool definitions in OpenAI function-calling format."""
        return [defn.to_openai_schema() for defn in self.list_tools()]

    def has_tool(self, name: str) -> bool:
        return name in self._tools
