"""Lead state machine — authoritative source of transition rules."""

from app.domain.entities.lead import LeadStatus
from app.domain.exceptions import InvalidStateTransition

# ── Single source of truth for valid transitions ─────────────────────
_ALLOWED_TRANSITIONS: dict[LeadStatus, frozenset[LeadStatus]] = {
    LeadStatus.INIT: frozenset({LeadStatus.COLLECTING_REQUIREMENTS}),
    LeadStatus.COLLECTING_REQUIREMENTS: frozenset({LeadStatus.VALIDATING_BUDGET}),
    LeadStatus.VALIDATING_BUDGET: frozenset({LeadStatus.MATCHING_PROPERTIES}),
    LeadStatus.MATCHING_PROPERTIES: frozenset({LeadStatus.NEGOTIATING}),
    LeadStatus.NEGOTIATING: frozenset({LeadStatus.CONFIRMING}),
    LeadStatus.CONFIRMING: frozenset({LeadStatus.INTERESTED, LeadStatus.NOT_INTERESTED}),
    LeadStatus.INTERESTED: frozenset({LeadStatus.CLOSED}),
    LeadStatus.NOT_INTERESTED: frozenset({LeadStatus.CLOSED}),
    LeadStatus.CLOSED: frozenset(),
}


class LeadStateMachine:
    """Validates and enforces lead state transitions.

    This class is the **single authoritative source** for all transition
    rules.  The Lead entity delegates to it — it never checks transitions
    on its own.
    """

    # Expose a read-only copy so tests can inspect it without mutation
    allowed_transitions: dict[LeadStatus, frozenset[LeadStatus]] = _ALLOWED_TRANSITIONS

    @staticmethod
    def validate_transition(current: LeadStatus, target: LeadStatus) -> None:
        """Raise ``InvalidStateTransition`` if the move is not allowed."""
        allowed = _ALLOWED_TRANSITIONS.get(current, frozenset())
        if target not in allowed:
            raise InvalidStateTransition(current.value, target.value)

    @staticmethod
    def can_transition(current: LeadStatus, target: LeadStatus) -> bool:
        """Return ``True`` if the transition is valid, ``False`` otherwise."""
        allowed = _ALLOWED_TRANSITIONS.get(current, frozenset())
        return target in allowed

    @staticmethod
    def get_allowed(current: LeadStatus) -> frozenset[LeadStatus]:
        """Return the set of states reachable from *current*."""
        return _ALLOWED_TRANSITIONS.get(current, frozenset())
