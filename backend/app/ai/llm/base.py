"""Abstract LLM client — vendor-agnostic interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCallResult:
    """Structured representation of a tool call returned by the LLM."""

    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMResponse:
    """Response from any LLM provider."""

    message: str
    tool_call: ToolCallResult | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


class LLMClient(ABC):
    """Abstract LLM client — implement per provider.

    The orchestrator depends only on this interface, keeping the system
    vendor-agnostic.
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        """Send messages + tool definitions and return a structured response."""
        ...
