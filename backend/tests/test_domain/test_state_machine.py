"""Tests for the state machine validation layer."""

import pytest

from app.domain.entities.lead import LeadStatus
from app.domain.exceptions import InvalidStateTransition
from app.domain.state_machine.lead_state_machine import LeadStateMachine


@pytest.fixture
def sm() -> LeadStateMachine:
    return LeadStateMachine()


class TestSingleSourceOfTruth:
    def test_allowed_transitions_covers_all_statuses(self) -> None:
        for status in LeadStatus:
            assert status in LeadStateMachine.allowed_transitions

    def test_closed_has_empty_transitions(self) -> None:
        assert LeadStateMachine.allowed_transitions[LeadStatus.CLOSED] == frozenset()


class TestValidateTransition:
    def test_valid_transition_passes(self, sm: LeadStateMachine) -> None:
        sm.validate_transition(LeadStatus.INIT, LeadStatus.COLLECTING_REQUIREMENTS)

    def test_invalid_transition_raises(self, sm: LeadStateMachine) -> None:
        with pytest.raises(InvalidStateTransition) as exc_info:
            sm.validate_transition(LeadStatus.INIT, LeadStatus.CLOSED)
        assert "INIT" in str(exc_info.value)
        assert "CLOSED" in str(exc_info.value)


class TestCanTransition:
    def test_returns_true_for_valid(self, sm: LeadStateMachine) -> None:
        assert sm.can_transition(LeadStatus.INIT, LeadStatus.COLLECTING_REQUIREMENTS) is True

    def test_returns_false_for_invalid(self, sm: LeadStateMachine) -> None:
        assert sm.can_transition(LeadStatus.INIT, LeadStatus.CLOSED) is False

    def test_closed_cannot_transition_anywhere(self, sm: LeadStateMachine) -> None:
        for target in LeadStatus:
            if target == LeadStatus.CLOSED:
                continue
            assert sm.can_transition(LeadStatus.CLOSED, target) is False


class TestGetAllowed:
    def test_init_has_one_target(self, sm: LeadStateMachine) -> None:
        allowed = sm.get_allowed(LeadStatus.INIT)
        assert allowed == frozenset({LeadStatus.COLLECTING_REQUIREMENTS})

    def test_confirming_has_two_targets(self, sm: LeadStateMachine) -> None:
        allowed = sm.get_allowed(LeadStatus.CONFIRMING)
        assert allowed == frozenset({LeadStatus.INTERESTED, LeadStatus.NOT_INTERESTED})

    def test_closed_has_no_targets(self, sm: LeadStateMachine) -> None:
        allowed = sm.get_allowed(LeadStatus.CLOSED)
        assert allowed == frozenset()
