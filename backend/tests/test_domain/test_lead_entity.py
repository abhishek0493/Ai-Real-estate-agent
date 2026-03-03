"""Tests for Lead entity and state transitions."""

from uuid import uuid4

import pytest

from app.domain.entities.lead import Lead, LeadStatus
from app.domain.exceptions import InvariantViolation, InvalidStateTransition


def _make_lead(**overrides) -> Lead:  # type: ignore[no-untyped-def]
    defaults = {"tenant_id": uuid4(), "name": "Alice", "email": "alice@example.com"}
    return Lead(**(defaults | overrides))


# ── Valid transitions ────────────────────────────────────────────────


class TestValidTransitions:
    """Walk through the full happy-path lifecycle."""

    def test_init_to_collecting(self) -> None:
        lead = _make_lead()
        lead.transition_to(LeadStatus.COLLECTING_REQUIREMENTS)
        assert lead.status == LeadStatus.COLLECTING_REQUIREMENTS

    def test_collecting_to_validating(self) -> None:
        lead = _make_lead(status=LeadStatus.COLLECTING_REQUIREMENTS)
        lead.transition_to(LeadStatus.VALIDATING_BUDGET)
        assert lead.status == LeadStatus.VALIDATING_BUDGET

    def test_validating_to_matching(self) -> None:
        lead = _make_lead(
            status=LeadStatus.VALIDATING_BUDGET,
            budget_min=100_000,
            budget_max=200_000,
            preferred_location="Mumbai",
        )
        lead.transition_to(LeadStatus.MATCHING_PROPERTIES)
        assert lead.status == LeadStatus.MATCHING_PROPERTIES

    def test_matching_to_negotiating(self) -> None:
        lead = _make_lead(status=LeadStatus.MATCHING_PROPERTIES)
        lead.transition_to(LeadStatus.NEGOTIATING)
        assert lead.status == LeadStatus.NEGOTIATING

    def test_negotiating_to_confirming(self) -> None:
        lead = _make_lead(status=LeadStatus.NEGOTIATING)
        lead.transition_to(LeadStatus.CONFIRMING)
        assert lead.status == LeadStatus.CONFIRMING

    def test_confirming_to_interested(self) -> None:
        lead = _make_lead(status=LeadStatus.CONFIRMING)
        lead.mark_interested()
        assert lead.status == LeadStatus.INTERESTED

    def test_confirming_to_not_interested(self) -> None:
        lead = _make_lead(status=LeadStatus.CONFIRMING)
        lead.mark_not_interested()
        assert lead.status == LeadStatus.NOT_INTERESTED

    def test_interested_to_closed(self) -> None:
        lead = _make_lead(status=LeadStatus.INTERESTED)
        lead.transition_to(LeadStatus.CLOSED)
        assert lead.status == LeadStatus.CLOSED

    def test_not_interested_to_closed(self) -> None:
        lead = _make_lead(status=LeadStatus.NOT_INTERESTED)
        lead.transition_to(LeadStatus.CLOSED)
        assert lead.status == LeadStatus.CLOSED


# ── Invalid transitions ─────────────────────────────────────────────


class TestInvalidTransitions:
    def test_init_to_negotiating_raises(self) -> None:
        lead = _make_lead()
        with pytest.raises(InvalidStateTransition):
            lead.transition_to(LeadStatus.NEGOTIATING)

    def test_closed_to_any_raises(self) -> None:
        lead = _make_lead(status=LeadStatus.CLOSED)
        for target in LeadStatus:
            if target == LeadStatus.CLOSED:
                continue
            with pytest.raises(InvalidStateTransition):
                lead.transition_to(target)

    def test_confirming_to_closed_directly_raises(self) -> None:
        lead = _make_lead(status=LeadStatus.CONFIRMING)
        with pytest.raises(InvalidStateTransition):
            lead.transition_to(LeadStatus.CLOSED)

    def test_init_to_closed_raises(self) -> None:
        lead = _make_lead()
        with pytest.raises(InvalidStateTransition):
            lead.transition_to(LeadStatus.CLOSED)


# ── Transition return value ──────────────────────────────────────────


class TestTransitionReturnValue:
    def test_returns_previous_and_new_status(self) -> None:
        lead = _make_lead()
        prev, new = lead.transition_to(LeadStatus.COLLECTING_REQUIREMENTS)
        assert prev == LeadStatus.INIT
        assert new == LeadStatus.COLLECTING_REQUIREMENTS

    def test_mark_interested_returns_tuple(self) -> None:
        lead = _make_lead(status=LeadStatus.CONFIRMING)
        prev, new = lead.mark_interested()
        assert prev == LeadStatus.CONFIRMING
        assert new == LeadStatus.INTERESTED

    def test_mark_not_interested_returns_tuple(self) -> None:
        lead = _make_lead(status=LeadStatus.CONFIRMING)
        prev, new = lead.mark_not_interested()
        assert prev == LeadStatus.CONFIRMING
        assert new == LeadStatus.NOT_INTERESTED


# ── Protected status ────────────────────────────────────────────────


class TestProtectedStatus:
    def test_status_is_property(self) -> None:
        lead = _make_lead()
        assert lead.status == LeadStatus.INIT

    def test_direct_status_assignment_raises(self) -> None:
        lead = _make_lead()
        with pytest.raises(AttributeError):
            lead.status = LeadStatus.CLOSED  # type: ignore[misc]

    def test_status_only_changes_via_transition(self) -> None:
        lead = _make_lead()
        assert lead.status == LeadStatus.INIT
        lead.transition_to(LeadStatus.COLLECTING_REQUIREMENTS)
        assert lead.status == LeadStatus.COLLECTING_REQUIREMENTS


# ── Domain invariants ────────────────────────────────────────────────


class TestDomainInvariants:
    def test_matching_without_location_raises(self) -> None:
        lead = _make_lead(
            status=LeadStatus.VALIDATING_BUDGET,
            budget_min=100_000,
            budget_max=200_000,
            preferred_location="",
        )
        with pytest.raises(InvariantViolation, match="preferred_location"):
            lead.transition_to(LeadStatus.MATCHING_PROPERTIES)

    def test_matching_without_budget_raises(self) -> None:
        lead = _make_lead(
            status=LeadStatus.VALIDATING_BUDGET,
            preferred_location="Mumbai",
        )
        with pytest.raises(InvariantViolation, match="Budget range"):
            lead.transition_to(LeadStatus.MATCHING_PROPERTIES)

    def test_matching_with_all_data_succeeds(self) -> None:
        lead = _make_lead(
            status=LeadStatus.VALIDATING_BUDGET,
            budget_min=100_000,
            budget_max=200_000,
            preferred_location="Mumbai",
        )
        lead.transition_to(LeadStatus.MATCHING_PROPERTIES)
        assert lead.status == LeadStatus.MATCHING_PROPERTIES


# ── Terminal state enforcement ───────────────────────────────────────


class TestTerminalState:
    def test_closed_is_terminal(self) -> None:
        lead = _make_lead(status=LeadStatus.CLOSED)
        for target in LeadStatus:
            if target == LeadStatus.CLOSED:
                continue
            with pytest.raises(InvalidStateTransition):
                lead.transition_to(target)


# ── Budget update ────────────────────────────────────────────────────


class TestBudgetUpdate:
    def test_valid_budget(self) -> None:
        lead = _make_lead()
        lead.update_budget(100_000, 200_000)
        assert lead.budget_min == 100_000
        assert lead.budget_max == 200_000

    def test_negative_budget_raises(self) -> None:
        lead = _make_lead()
        with pytest.raises(ValueError):
            lead.update_budget(-1, 200_000)

    def test_min_exceeds_max_raises(self) -> None:
        lead = _make_lead()
        with pytest.raises(ValueError):
            lead.update_budget(300_000, 200_000)
