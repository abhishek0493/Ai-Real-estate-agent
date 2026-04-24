"""Tests for ConversationStateManager — uses fakeredis for isolation."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

import fakeredis
import pytest
import pytest_asyncio

from app.ai.orchestrator.state_manager import ConversationStateManager
from app.domain.entities.lead import Lead, LeadId, LeadStatus


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def redis():
    """In-memory fake Redis instance — isolated per test."""
    server = fakeredis.FakeAsyncRedis(decode_responses=True)
    yield server
    await server.aclose()


@pytest.fixture
def manager(redis) -> ConversationStateManager:
    """State manager wired to the fake Redis."""
    return ConversationStateManager(
        redis=redis,
        key_prefix="test",
        ttl_seconds=3600,
    )


@pytest.fixture
def tenant_id() -> UUID:
    return uuid4()


@pytest.fixture
def lead(tenant_id) -> Lead:
    return Lead(
        id=LeadId(uuid4()),
        tenant_id=tenant_id,
        name="Test Buyer",
        email="buyer@example.com",
        phone="9876543210",
        budget_min=5_000_000,
        budget_max=10_000_000,
        preferred_location="Mumbai",
        bedrooms=2,
        preferences=["parking", "near station"],
        status=LeadStatus.COLLECTING_REQUIREMENTS,
    )


# ── Test: initialize ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_initialize_seeds_state(manager, lead, redis):
    """initialize() should create a hash in Redis with all lead fields."""
    state = await manager.initialize(lead)

    assert state["lead_id"] == str(lead.id)
    assert state["lead_status"] == "COLLECTING_REQUIREMENTS"
    assert state["lead_name"] == "Test Buyer"
    assert state["preferred_location"] == "Mumbai"
    assert state["budget_min"] == "5000000"
    assert state["budget_max"] == "10000000"
    assert state["bedrooms"] == "2"
    assert json.loads(state["preferences"]) == ["parking", "near station"]
    assert state["turn_count"] == "0"

    # Verify it's actually in Redis
    key = f"test:conv:{lead.id}:state"
    raw = await redis.hgetall(key)
    assert raw["lead_name"] == "Test Buyer"


@pytest.mark.asyncio
async def test_initialize_sets_ttl(manager, lead, redis):
    """initialize() should set a TTL on the state key."""
    await manager.initialize(lead)
    key = f"test:conv:{lead.id}:state"
    ttl = await redis.ttl(key)
    assert ttl > 0
    assert ttl <= 3600


# ── Test: get_state ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_state_returns_none_on_miss(manager):
    """get_state() should return None when no state exists."""
    result = await manager.get_state(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_state_round_trip(manager, lead):
    """initialize → get_state should return consistent data."""
    await manager.initialize(lead)
    state = await manager.get_state(lead.id)

    assert state is not None
    assert state["lead_status"] == "COLLECTING_REQUIREMENTS"
    assert state["budget_min"] == "5000000"


# ── Test: sync_from_lead ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sync_from_lead_updates_changed_fields(manager, lead):
    """sync_from_lead() should reflect mutations on the Lead entity."""
    await manager.initialize(lead)

    # Mutate the domain entity
    lead.preferred_location = "Pune"
    lead.update_budget(7_000_000, 15_000_000)

    updated = await manager.sync_from_lead(lead)
    assert updated["preferred_location"] == "Pune"
    assert updated["budget_min"] == "7000000"
    assert updated["budget_max"] == "15000000"

    # Verify via get_state too
    state = await manager.get_state(lead.id)
    assert state["preferred_location"] == "Pune"


@pytest.mark.asyncio
async def test_sync_from_lead_preserves_created_at(manager, lead):
    """sync_from_lead() should not overwrite the original created_at."""
    initial = await manager.initialize(lead)
    original_created = initial["created_at"]

    lead.preferred_location = "Delhi"
    updated = await manager.sync_from_lead(lead)

    assert updated["created_at"] == original_created
    assert updated["updated_at"] != original_created  # updated_at should change


# ── Test: record_turn ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_turn_increments_count(manager, lead, redis):
    """record_turn() should increment turn_count by 1 each call."""
    await manager.initialize(lead)

    await manager.record_turn(lead.id, tool_name="set_location", error=None)
    state = await manager.get_state(lead.id)
    assert state["turn_count"] == "1"
    assert state["last_tool"] == "set_location"
    assert state["last_tool_error"] == ""

    await manager.record_turn(lead.id, tool_name="update_budget", error=None)
    state = await manager.get_state(lead.id)
    assert state["turn_count"] == "2"
    assert state["last_tool"] == "update_budget"


@pytest.mark.asyncio
async def test_record_turn_records_error(manager, lead):
    """record_turn() should store the error string when provided."""
    await manager.initialize(lead)
    await manager.record_turn(lead.id, tool_name="validate_budget", error="Budget too low")

    state = await manager.get_state(lead.id)
    assert state["last_tool_error"] == "Budget too low"


@pytest.mark.asyncio
async def test_record_turn_with_no_tool(manager, lead):
    """record_turn() with tool_name=None should set last_tool to empty."""
    await manager.initialize(lead)
    await manager.record_turn(lead.id, tool_name=None, error=None)

    state = await manager.get_state(lead.id)
    assert state["turn_count"] == "1"
    assert state["last_tool"] == ""


# ── Test: message summaries ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_append_and_get_message_summaries(manager, lead):
    """Summaries should be appended and retrievable in order."""
    await manager.initialize(lead)

    await manager.append_message_summary(lead.id, "user", "I want a 2BHK in Mumbai")
    await manager.append_message_summary(lead.id, "assistant", "Great! What's your budget?")

    summaries = await manager.get_message_summaries(lead.id, count=10)
    assert len(summaries) == 2
    assert summaries[0]["role"] == "user"
    assert summaries[0]["snippet"] == "I want a 2BHK in Mumbai"
    assert summaries[1]["role"] == "assistant"
    assert "ts" in summaries[1]


@pytest.mark.asyncio
async def test_message_summaries_capped(manager, lead):
    """The history list should be capped at _MAX_HISTORY_LEN entries."""
    await manager.initialize(lead)

    # Push 40 entries — should be capped at 30
    for i in range(40):
        await manager.append_message_summary(lead.id, "user", f"Message {i}")

    summaries = await manager.get_message_summaries(lead.id, count=50)
    assert len(summaries) == 30  # capped

    # The oldest should be message 10 (40 - 30)
    assert summaries[0]["snippet"] == "Message 10"


@pytest.mark.asyncio
async def test_message_snippet_truncated(manager, lead):
    """Snippets longer than 200 chars should be truncated."""
    await manager.initialize(lead)
    long_text = "x" * 500
    await manager.append_message_summary(lead.id, "user", long_text)

    summaries = await manager.get_message_summaries(lead.id, count=1)
    assert len(summaries[0]["snippet"]) == 200


# ── Test: delete_state / is_active ───────────────────────────────────


@pytest.mark.asyncio
async def test_is_active_true_after_initialize(manager, lead):
    """is_active() should return True when state exists."""
    await manager.initialize(lead)
    assert await manager.is_active(lead.id) is True


@pytest.mark.asyncio
async def test_is_active_false_on_miss(manager):
    """is_active() should return False when no state exists."""
    assert await manager.is_active(uuid4()) is False


@pytest.mark.asyncio
async def test_delete_state_removes_everything(manager, lead):
    """delete_state() should remove both state hash and history list."""
    await manager.initialize(lead)
    await manager.append_message_summary(lead.id, "user", "Hello")

    assert await manager.is_active(lead.id) is True

    await manager.delete_state(lead.id)

    assert await manager.is_active(lead.id) is False
    summaries = await manager.get_message_summaries(lead.id, count=10)
    assert summaries == []


# ── Test: empty lead fields ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_initialize_with_minimal_lead(manager, tenant_id):
    """A lead with no optional fields should still initialize cleanly."""
    minimal_lead = Lead(
        tenant_id=tenant_id,
        name="Anonymous",
        email="",
        status=LeadStatus.INIT,
    )

    state = await manager.initialize(minimal_lead)
    assert state["lead_status"] == "INIT"
    assert state["preferred_location"] == ""
    assert state["budget_min"] == ""
    assert state["budget_max"] == ""
    assert state["bedrooms"] == ""
    assert json.loads(state["preferences"]) == []
