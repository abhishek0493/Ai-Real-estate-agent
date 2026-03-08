"""AI Orchestrator — the main engine driving LLM ↔ domain interaction."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.ai.llm.base import LLMClient, ToolCallResult
from app.ai.orchestrator.prompt_builder import PromptBuilder
from app.ai.tools.registry import ToolRegistry
from app.ai.tools.schema import ToolCall
from app.ai.tools.validator import ToolValidationError, ToolValidator
from app.domain.entities.lead import Lead, LeadStatus
from app.domain.exceptions import DomainException

logger = logging.getLogger(__name__)


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
        3. If tool_call → validate → execute → follow-up LLM call → return
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
            return await self._execute_tool(
                lead, llm_response.tool_call, messages, tool_schemas,
            )

        # 4. Plain message
        return AIResponse(
            assistant_message=llm_response.message,
            updated_state=lead.status.value,
        )

    async def _execute_tool(
        self,
        lead: Lead,
        tool_call_result: ToolCallResult,
        messages: list[dict[str, str]],
        tool_schemas: list[dict[str, Any]],
    ) -> AIResponse:
        """Validate and execute a tool call, then ask the LLM to respond."""
        tool_call = ToolCall(name=tool_call_result.name, arguments=tool_call_result.arguments)

        # Validate — on failure, recover gracefully
        try:
            self._validator.validate(tool_call, lead.status)
        except ToolValidationError as e:
            logger.warning(
                "Tool validation failed: tool=%s state=%s error=%s",
                tool_call.name, lead.status.value, e.message,
            )
            return await self._recover_from_error(
                lead, messages, tool_schemas, e.message,
            )

        # Execute — on failure, recover gracefully
        entry = self._registry.get_tool(tool_call.name)
        assert entry is not None  # validator already checked existence
        _, handler = entry

        try:
            result = await handler(lead, **tool_call.arguments)
        except DomainException as e:
            logger.warning(
                "Domain exception during tool execution: tool=%s error=%s",
                tool_call.name, e.message,
            )
            return await self._recover_from_error(
                lead, messages, tool_schemas, e.message,
                executed_tool=tool_call.name,
            )

        # Follow-up LLM call: tell the LLM what happened and let it
        # generate a natural conversational response for the user.
        follow_up_messages = messages + [
            {
                "role": "assistant",
                "content": (
                    f"[Tool executed: {tool_call.name} "
                    f"with args {tool_call.arguments}. "
                    f"Result: {result}. "
                    f"Lead status is now: {lead.status.value}]"
                ),
            },
            {
                "role": "user",
                "content": (
                    "Now respond naturally to the user based on the tool result. "
                    "Do NOT mention tool names or internal status codes. "
                    "Be conversational and helpful."
                ),
            },
        ]

        follow_up = await self._llm.chat(follow_up_messages, tool_schemas)
        assistant_message = follow_up.message or f"Executed {tool_call.name}."

        return AIResponse(
            assistant_message=assistant_message,
            executed_tool=tool_call.name,
            tool_result=result,
            updated_state=lead.status.value,
        )

    async def _recover_from_error(
        self,
        lead: Lead,
        messages: list[dict[str, str]],
        tool_schemas: list[dict[str, Any]],
        error_detail: str,
        executed_tool: str | None = None,
    ) -> AIResponse:
        """Ask the LLM to generate a natural recovery response.

        Instead of exposing internal errors to the user, we tell the LLM
        what went wrong and ask it to continue the conversation with a
        helpful follow-up question.
        """
        recovery_messages = messages + [
            {
                "role": "system",
                "content": (
                    f"An internal action could not be completed: {error_detail}. "
                    "Do NOT tell the user about this error. Instead, continue the "
                    "conversation naturally. Ask the next logical clarifying question "
                    "to gather the information needed. For example, ask about their "
                    "budget, preferred location, or number of bedrooms. "
                    "Be helpful and conversational."
                ),
            },
        ]

        recovery = await self._llm.chat(recovery_messages, tool_schemas)
        fallback = (
            recovery.message
            or "I'm gathering some details to find the best property options for you. "
               "Could you tell me more about what you're looking for?"
        )

        return AIResponse(
            assistant_message=fallback,
            executed_tool=executed_tool,
            error=error_detail,
            updated_state=lead.status.value,
        )
