"""Tool definition and tool call schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolDefinition:
    """Describes a tool that the LLM may invoke.

    ``parameters`` follows JSON Schema format so it can be sent directly
    to OpenAI-compatible APIs.
    """

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function-calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass(frozen=True)
class ToolCall:
    """A validated tool invocation (name + arguments)."""

    name: str
    arguments: dict[str, Any]
