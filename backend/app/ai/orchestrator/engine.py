"""AI Orchestrator — the main engine driving LLM ↔ domain interaction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.ai.llm.base import LLMClient, ToolCallResult
from app.ai.orchestrator.prompt_builder import PromptBuilder
from app.ai.tools.registry import ToolRegistry
from app.ai.tools.schema import ToolCall
from app.ai.tools.validator import ToolValidationError, ToolValidator
from app.domain.entities.lead import Lead, LeadStatus
from app.domain.exceptions import DomainException


@dataclass(frozen=True)
class AIResponse:
    """Structured response from the orchestrator back to the caller."""

    assistant_message: str
    executed_tool: str | None = None
    tool_result: dict[str, Any] = field(default_factory=dict)
    updated_state: str | None = None
    error: str | None = None


class AIOrchestrator:
    """Drives the LLM → validate → execute → respond pipeline.

    The orchestrator:
    1. Builds a prompt with the current lead context.
    2. Calls the LLM.
    3. If the LLM returns a tool call, validates and executes it safely.
    4. Returns a structured ``AIResponse``.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        registry: ToolRegistry,
        prompt_version: str = "v1",
    ) -> None:
        self._llm = llm_client
        self._registry = registry
        self._validator = ToolValidator(registry)
        self._prompt_builder = PromptBuilder(version=prompt_version)

    async def process_message(
        self,
        lead: Lead,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> AIResponse:
        """Process a user message and return an AI response.

        Flow:
        1. Build prompt (system + history + user message)
        2. Call LLMClient.chat()
        3. If tool_call → validate → execute → return result
        4. Else → return assistant message only
        """
        history = conversation_history or []
        allowed_tool_names = [t.name for t in self._registry.list_tools()]

        # 1. Build prompt
        messages = self._prompt_builder.build_messages(
            lead=lead,
            user_message=user_message,
            conversation_history=history,
            allowed_tools=allowed_tool_names,
        )

        # 2. Call LLM
        tool_schemas = self._registry.list_openai_schemas()
        llm_response = await self._llm.chat(messages, tool_schemas)

        # 3. Handle tool call
        if llm_response.tool_call is not None:
            return await self._execute_tool(lead, llm_response.tool_call, llm_response.message)

        # 4. Plain message
        return AIResponse(
            assistant_message=llm_response.message,
            updated_state=lead.status.value,
        )

    async def _execute_tool(
        self,
        lead: Lead,
        tool_call_result: ToolCallResult,
        llm_message: str,
    ) -> AIResponse:
        """Validate and execute a tool call safely."""
        tool_call = ToolCall(name=tool_call_result.name, arguments=tool_call_result.arguments)

        # Validate
        try:
            self._validator.validate(tool_call, lead.status)
        except ToolValidationError as e:
            return AIResponse(
                assistant_message=f"I tried to use a tool but it was not allowed: {e.message}",
                error=e.message,
                updated_state=lead.status.value,
            )

        # Execute
        entry = self._registry.get_tool(tool_call.name)
        assert entry is not None  # validator already checked existence
        _, handler = entry

        try:
            result = await handler(lead, **tool_call.arguments)
        except DomainException as e:
            return AIResponse(
                assistant_message=f"Action failed: {e.message}",
                executed_tool=tool_call.name,
                error=e.message,
                updated_state=lead.status.value,
            )

        return AIResponse(
            assistant_message=llm_message or f"Executed {tool_call.name}.",
            executed_tool=tool_call.name,
            tool_result=result,
            updated_state=lead.status.value,
        )
