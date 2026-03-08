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
    """LLM client that returns preconfigured responses in sequence.

    If a single response is given, it is returned for every call.
    If multiple responses are given, they are returned in order.
    """

    def __init__(self, *responses: LLMResponse) -> None:
        self._responses = list(responses)
        self._call_index = 0

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
    ) -> LLMResponse:
        if len(self._responses) == 1:
            return self._responses[0]
        resp = self._responses[min(self._call_index, len(self._responses) - 1)]
        self._call_index += 1
        return resp


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


# ── Orchestrator: graceful recovery on unknown tool ──────────────────


class TestGracefulRecovery:
    @pytest.mark.asyncio
    async def test_unknown_tool_recovers_gracefully(self, registry: ToolRegistry) -> None:
        """When the LLM calls an unknown tool, the orchestrator should
        recover with a natural response — never expose the raw error."""
        llm = MockLLMClient(
            # First call: LLM tries an unknown tool
            LLMResponse(
                message="Let me check.",
                tool_call=ToolCallResult(name="drop_database", arguments={}),
            ),
            # Second call: recovery LLM response
            LLMResponse(message="Could you tell me what area you're looking in?"),
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead()

        result = await orchestrator.process_message(lead, "Drop the database")

        # Error is recorded internally but NOT shown to user
        assert result.error is not None
        assert "Unknown tool" in result.error
        # The user-facing message is from the recovery LLM call
        assert "drop_database" not in result.assistant_message.lower()
        assert "Could you tell me" in result.assistant_message
        assert result.executed_tool is None

    @pytest.mark.asyncio
    async def test_wrong_state_tool_recovers_gracefully(self, registry: ToolRegistry) -> None:
        """When a tool is not allowed in the current state, the user
        gets a natural follow-up question, not an error message."""
        llm = MockLLMClient(
            # First call: LLM tries start_negotiation in INIT state
            LLMResponse(
                message="Starting negotiation.",
                tool_call=ToolCallResult(name="start_negotiation", arguments={}),
            ),
            # Second call: recovery response
            LLMResponse(message="I'd love to help! What location are you interested in?"),
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead()  # status is INIT

        result = await orchestrator.process_message(lead, "Let's negotiate")

        assert result.error is not None
        assert "not allowed" in result.error
        # User never sees the error
        assert "not allowed" not in result.assistant_message
        assert "I'd love to help" in result.assistant_message
        assert lead.status == LeadStatus.INIT  # unchanged

    @pytest.mark.asyncio
    async def test_missing_params_recovers_gracefully(self, registry: ToolRegistry) -> None:
        """Missing required params trigger graceful recovery."""
        llm = MockLLMClient(
            LLMResponse(
                message="Updating budget.",
                tool_call=ToolCallResult(
                    name="update_budget",
                    arguments={"budget_min": 100_000},  # missing budget_max
                ),
            ),
            LLMResponse(message="What's the upper end of your budget range?"),
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead(status=LeadStatus.COLLECTING_REQUIREMENTS)

        result = await orchestrator.process_message(lead, "My budget is 100k")

        assert result.error is not None
        assert "budget_max" in result.error
        # User-facing message is natural
        assert "budget_max" not in result.assistant_message
        assert "budget" in result.assistant_message.lower()


# ── Orchestrator: update_preferences tool ────────────────────────────


class TestPreferencesTool:
    @pytest.mark.asyncio
    async def test_update_preferences_stores_values(self, registry: ToolRegistry) -> None:
        llm = MockLLMClient(
            LLMResponse(
                message="Noted your preferences.",
                tool_call=ToolCallResult(
                    name="update_preferences",
                    arguments={"preferences": ["parking", "near station"]},
                ),
            ),
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead(status=LeadStatus.COLLECTING_REQUIREMENTS)

        result = await orchestrator.process_message(lead, "I want parking and near station")

        assert result.executed_tool == "update_preferences"
        assert result.error is None
        assert "parking" in lead.preferences
        assert "near station" in lead.preferences

    @pytest.mark.asyncio
    async def test_preferences_accumulate(self, registry: ToolRegistry) -> None:
        """Multiple preference updates should merge, not overwrite."""
        llm = MockLLMClient(
            LLMResponse(
                message="Got it.",
                tool_call=ToolCallResult(
                    name="update_preferences",
                    arguments={"preferences": ["balcony"]},
                ),
            ),
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead(
            status=LeadStatus.COLLECTING_REQUIREMENTS,
            preferences=["parking"],
        )

        result = await orchestrator.process_message(lead, "Also a balcony")

        assert "parking" in lead.preferences
        assert "balcony" in lead.preferences

    @pytest.mark.asyncio
    async def test_preferences_not_allowed_in_init(self, registry: ToolRegistry) -> None:
        """update_preferences is only allowed in COLLECTING_REQUIREMENTS."""
        llm = MockLLMClient(
            LLMResponse(
                message="Noting preferences.",
                tool_call=ToolCallResult(
                    name="update_preferences",
                    arguments={"preferences": ["parking"]},
                ),
            ),
            LLMResponse(message="Let's start from the beginning! What are you looking for?"),
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead()  # INIT state

        result = await orchestrator.process_message(lead, "I want parking")

        assert result.error is not None
        assert "not allowed" in result.error


# ── Orchestrator: invalid state transition ───────────────────────────


class TestInvalidTransition:
    @pytest.mark.asyncio
    async def test_domain_exception_caught(self, registry: ToolRegistry) -> None:
        """If a tool is in the allowlist for a state but the domain rejects
        the transition, the orchestrator should recover gracefully."""
        llm = MockLLMClient(
            LLMResponse(
                message="Confirming interest.",
                tool_call=ToolCallResult(name="confirm_interest", arguments={"interested": True}),
            ),
            LLMResponse(message="Let me get a few more details first."),
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead(status=LeadStatus.CONFIRMING)

        result = await orchestrator.process_message(lead, "Yes I'm interested")

        assert result.error is not None
        assert result.executed_tool == "confirm_interest"
        # User-facing message should be the recovery response
        assert "error" not in result.assistant_message.lower()


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

    def test_update_preferences_allowed_in_collecting(self, registry: ToolRegistry) -> None:
        validator = ToolValidator(registry)
        # Should not raise
        validator.validate(
            ToolCall(name="update_preferences", arguments={"preferences": ["parking"]}),
            LeadStatus.COLLECTING_REQUIREMENTS,
        )

    def test_set_bedrooms_allowed_in_collecting(self, registry: ToolRegistry) -> None:
        validator = ToolValidator(registry)
        # Should not raise
        validator.validate(
            ToolCall(name="set_bedrooms", arguments={"bedrooms": 2}),
            LeadStatus.COLLECTING_REQUIREMENTS,
        )


# ── Tool registry unit tests ────────────────────────────────────────


class TestToolRegistryUnit:
    def test_list_tools_returns_all(self, registry: ToolRegistry) -> None:
        tools = registry.list_tools()
        assert len(tools) == 11  # 9 original + update_preferences + set_bedrooms

    def test_get_unknown_returns_none(self, registry: ToolRegistry) -> None:
        assert registry.get_tool("nonexistent") is None

    def test_has_tool(self, registry: ToolRegistry) -> None:
        assert registry.has_tool("update_budget") is True
        assert registry.has_tool("update_preferences") is True
        assert registry.has_tool("set_bedrooms") is True
        assert registry.has_tool("nonexistent") is False

    def test_openai_schemas_format(self, registry: ToolRegistry) -> None:
        schemas = registry.list_openai_schemas()
        assert all(s["type"] == "function" for s in schemas)
        assert all("function" in s for s in schemas)


# ── Lead entity: new fields ──────────────────────────────────────────


class TestLeadNewFields:
    def test_lead_defaults_for_new_fields(self) -> None:
        lead = _make_lead()
        assert lead.bedrooms is None
        assert lead.preferences == []

    def test_lead_accepts_bedrooms_and_preferences(self) -> None:
        lead = _make_lead(bedrooms=3, preferences=["parking", "near station"])
        assert lead.bedrooms == 3
        assert "parking" in lead.preferences
        assert "near station" in lead.preferences


class TestSetBedroomsTool:
    @pytest.mark.asyncio
    async def test_set_bedrooms_stores_value(self, registry: ToolRegistry) -> None:
        llm = MockLLMClient(
            LLMResponse(
                message="Got it, 2 BHK.",
                tool_call=ToolCallResult(
                    name="set_bedrooms",
                    arguments={"bedrooms": 2},
                ),
            ),
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead(status=LeadStatus.COLLECTING_REQUIREMENTS)

        result = await orchestrator.process_message(lead, "I want a 2 BHK")

        assert result.executed_tool == "set_bedrooms"
        assert result.error is None
        assert lead.bedrooms == 2

    @pytest.mark.asyncio
    async def test_set_bedrooms_not_allowed_in_init(self, registry: ToolRegistry) -> None:
        llm = MockLLMClient(
            LLMResponse(
                message="Setting bedrooms.",
                tool_call=ToolCallResult(name="set_bedrooms", arguments={"bedrooms": 3}),
            ),
            LLMResponse(message="Let's start by understanding your needs."),
        )
        orchestrator = AIOrchestrator(llm, registry)
        lead = _make_lead()  # INIT state

        result = await orchestrator.process_message(lead, "3 BHK")

        assert result.error is not None
