"""Unit tests for the AI orchestrator — LLM is always mocked."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from app.ai.llm.base import LLMClient, LLMResponse, ToolCallResult
from app.ai.orchestrator.engine import AIOrchestrator, AIResponse
from app.ai.tools import build_default_registry
from app.ai.tools.registry import ToolRegistry
from app.ai.tools.schema import ToolCall, ToolDefinition
from app.ai.tools.validator import ToolValidationError, ToolValidator
from app.domain.entities.lead import Lead, LeadStatus


# ── Helpers ──────────────────────────────────────────────────────────


def _make_lead(**overrides: Any) -> Lead:
    defaults: dict[str, Any] = {
        "tenant_id": uuid4(),
        "name": "Test User",
        "email": "test@example.com",
        "budget_min": 100_000,
        "budget_max": 300_000,
        "preferred_location": "Mumbai",
    }
    return Lead(**(defaults | overrides))


class MockLLMClient(LLMClient):
    """LLM client that returns a preconfigured response."""

    def __init__(self, response: LLMResponse) -> None:
        self._response = response

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        return self._response


@pytest.fixture
def registry() -> ToolRegistry:
    return build_default_registry()


# ── Orchestrator: plain message ──────────────────────────────────────


class TestPlainMessage:
    @pytest.mark.asyncio
    async def test_plain_llm_response(self, registry: ToolRegistry) -> None:
        llm = MockLLMClient(LLMResponse(message="Hello! How can I help you?"))
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead()

        result = await orchestrator.process_message(lead, "Hi")

        assert result.assistant_message == "Hello! How can I help you?"
        assert result.executed_tool is None
        assert result.error is None
        assert result.updated_state == LeadStatus.INIT.value


# ── Orchestrator: valid tool call ────────────────────────────────────


class TestValidToolCall:
    @pytest.mark.asyncio
    async def test_start_collection_tool(self, registry: ToolRegistry) -> None:
        llm = MockLLMClient(
            LLMResponse(
                message="Let me start collecting your requirements.",
                tool_call=ToolCallResult(name="start_collection", arguments={}),
            )
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead()

        result = await orchestrator.process_message(lead, "I want to buy a house")

        assert result.executed_tool == "start_collection"
        assert result.error is None
        assert lead.status == LeadStatus.COLLECTING_REQUIREMENTS
        assert result.updated_state == LeadStatus.COLLECTING_REQUIREMENTS.value

    @pytest.mark.asyncio
    async def test_update_budget_tool(self, registry: ToolRegistry) -> None:
        llm = MockLLMClient(
            LLMResponse(
                message="Got it, updating your budget.",
                tool_call=ToolCallResult(
                    name="update_budget",
                    arguments={"budget_min": 150_000, "budget_max": 250_000},
                ),
            )
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead(status=LeadStatus.COLLECTING_REQUIREMENTS)

        result = await orchestrator.process_message(lead, "My budget is 150k-250k")

        assert result.executed_tool == "update_budget"
        assert lead.budget_min == 150_000
        assert lead.budget_max == 250_000


# ── Orchestrator: unknown tool ───────────────────────────────────────


class TestUnknownTool:
    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, registry: ToolRegistry) -> None:
        llm = MockLLMClient(
            LLMResponse(
                message="Let me check.",
                tool_call=ToolCallResult(name="drop_database", arguments={}),
            )
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead()

        result = await orchestrator.process_message(lead, "Drop the database")

        assert result.error is not None
        assert "Unknown tool" in result.error
        assert result.executed_tool is None


# ── Orchestrator: wrong state ────────────────────────────────────────


class TestWrongState:
    @pytest.mark.asyncio
    async def test_tool_not_allowed_in_state(self, registry: ToolRegistry) -> None:
        llm = MockLLMClient(
            LLMResponse(
                message="Starting negotiation.",
                tool_call=ToolCallResult(name="start_negotiation", arguments={}),
            )
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead()  # status is INIT — cannot negotiate yet

        result = await orchestrator.process_message(lead, "Let's negotiate")

        assert result.error is not None
        assert "not allowed" in result.error
        assert lead.status == LeadStatus.INIT  # unchanged


# ── Orchestrator: invalid state transition ───────────────────────────


class TestInvalidTransition:
    @pytest.mark.asyncio
    async def test_domain_exception_caught(self, registry: ToolRegistry) -> None:
        """If a tool is in the allowlist for a state but the domain rejects
        the transition, the orchestrator should catch it gracefully."""
        llm = MockLLMClient(
            LLMResponse(
                message="Confirming interest.",
                tool_call=ToolCallResult(name="confirm_interest", arguments={"interested": True}),
            )
        )
        orchestrator = AIOrchestrator(llm, registry)
        # CONFIRMING state allows confirm_interest but domain re-validates
        lead = _make_lead(status=LeadStatus.CONFIRMING)

        # confirm_interest handler calls flow.confirm_interest() which does
        # NEGOTIATING→CONFIRMING first — but lead is already CONFIRMING,
        # so the domain raises InvalidStateTransition
        result = await orchestrator.process_message(lead, "Yes I'm interested")

        assert result.error is not None
        assert result.executed_tool == "confirm_interest"


# ── Orchestrator: missing required params ────────────────────────────


class TestMissingParams:
    @pytest.mark.asyncio
    async def test_missing_param_returns_error(self, registry: ToolRegistry) -> None:
        llm = MockLLMClient(
            LLMResponse(
                message="Updating budget.",
                tool_call=ToolCallResult(
                    name="update_budget",
                    arguments={"budget_min": 100_000},  # missing budget_max
                ),
            )
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead(status=LeadStatus.COLLECTING_REQUIREMENTS)

        result = await orchestrator.process_message(lead, "My budget is 100k")

        assert result.error is not None
        assert "budget_max" in result.error


# ── Tool validator unit tests ────────────────────────────────────────


class TestToolValidatorUnit:
    def test_unknown_tool_raises(self, registry: ToolRegistry) -> None:
        validator = ToolValidator(registry)
        with pytest.raises(ToolValidationError, match="Unknown tool"):
            validator.validate(ToolCall(name="foo", arguments={}), LeadStatus.INIT)

    def test_missing_required_param_raises(self, registry: ToolRegistry) -> None:
        validator = ToolValidator(registry)
        with pytest.raises(ToolValidationError, match="budget_max"):
            validator.validate(
                ToolCall(name="update_budget", arguments={"budget_min": 1}),
                LeadStatus.COLLECTING_REQUIREMENTS,
            )

    def test_tool_not_in_state_raises(self, registry: ToolRegistry) -> None:
        validator = ToolValidator(registry)
        with pytest.raises(ToolValidationError, match="not allowed"):
            validator.validate(
                ToolCall(name="start_negotiation", arguments={}),
                LeadStatus.INIT,
            )

    def test_valid_tool_passes(self, registry: ToolRegistry) -> None:
        validator = ToolValidator(registry)
        # Should not raise
        validator.validate(
            ToolCall(name="start_collection", arguments={}),
            LeadStatus.INIT,
        )


# ── Tool registry unit tests ────────────────────────────────────────


class TestToolRegistryUnit:
    def test_list_tools_returns_all(self, registry: ToolRegistry) -> None:
        tools = registry.list_tools()
        assert len(tools) == 9

    def test_get_unknown_returns_none(self, registry: ToolRegistry) -> None:
        assert registry.get_tool("nonexistent") is None

    def test_has_tool(self, registry: ToolRegistry) -> None:
        assert registry.has_tool("update_budget") is True
        assert registry.has_tool("nonexistent") is False

    def test_openai_schemas_format(self, registry: ToolRegistry) -> None:
        schemas = registry.list_openai_schemas()
        assert all(s["type"] == "function" for s in schemas)
        assert all("function" in s for s in schemas)
