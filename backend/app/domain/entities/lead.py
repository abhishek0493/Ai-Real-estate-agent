"""Lead entity and related value objects — pure domain layer."""

from __future__ import annotations

from enum import Enum
from typing import NewType
from uuid import UUID, uuid4

from app.domain.exceptions import InvariantViolation

LeadId = NewType("LeadId", UUID)


class LeadStatus(str, Enum):
    """All possible states a lead can be in."""

    INIT = "INIT"
    COLLECTING_REQUIREMENTS = "COLLECTING_REQUIREMENTS"
    VALIDATING_BUDGET = "VALIDATING_BUDGET"
    MATCHING_PROPERTIES = "MATCHING_PROPERTIES"
    NEGOTIATING = "NEGOTIATING"
    CONFIRMING = "CONFIRMING"
    INTERESTED = "INTERESTED"
    NOT_INTERESTED = "NOT_INTERESTED"
    CLOSED = "CLOSED"


class Lead:
    """Core lead entity — owns its state, delegates validation to the state machine.

    ``status`` is a read-only property. The only way to change it is through
    ``transition_to()``, which delegates to ``LeadStateMachine``.
    """

    def __init__(
        self,
        *,
        tenant_id: UUID,
        name: str,
        email: str,
        phone: str = "",
        budget_min: float | None = None,
        budget_max: float | None = None,
        preferred_location: str = "",
        bedrooms: int | None = None,
        preferences: list[str] | None = None,
        status: LeadStatus = LeadStatus.INIT,
        id: LeadId | None = None,
    ) -> None:
        self.id: LeadId = id or LeadId(uuid4())
        self.tenant_id = tenant_id
        self.name = name
        self.email = email
        self.phone = phone
        self.budget_min = budget_min
        self.budget_max = budget_max
        self.preferred_location = preferred_location
        self.bedrooms = bedrooms
        self.preferences: list[str] = preferences or []
        self._status = status

    # ── Status (read-only property) ──────────────────────────────────

    @property
    def status(self) -> LeadStatus:
        return self._status

    # ── State transitions ────────────────────────────────────────────

    def transition_to(self, new_status: LeadStatus) -> tuple[LeadStatus, LeadStatus]:
        """Move the lead to *new_status*.

        Validation is delegated to ``LeadStateMachine`` (the single
        source of truth).  Domain invariants are checked **before** the
        transition is committed.

        Returns:
            ``(previous_status, new_status)`` — useful for audit logging.
        """
        # Import here to avoid circular dependency at module level
        from app.domain.state_machine.lead_state_machine import LeadStateMachine

        LeadStateMachine.validate_transition(self._status, new_status)
        self._check_invariants(new_status)
        previous = self._status
        self._status = new_status
        return (previous, new_status)

    # ── Convenience methods ──────────────────────────────────────────

    def mark_interested(self) -> tuple[LeadStatus, LeadStatus]:
        """CONFIRMING → INTERESTED."""
        return self.transition_to(LeadStatus.INTERESTED)

    def mark_not_interested(self) -> tuple[LeadStatus, LeadStatus]:
        """CONFIRMING → NOT_INTERESTED."""
        return self.transition_to(LeadStatus.NOT_INTERESTED)

    def update_budget(self, budget_min: float, budget_max: float) -> None:
        """Set the buyer's budget range with validation."""
        if budget_min < 0 or budget_max < 0:
            raise ValueError("Budget values must be non-negative")
        if budget_min > budget_max:
            raise ValueError("budget_min cannot exceed budget_max")
        self.budget_min = budget_min
        self.budget_max = budget_max

    # ── Invariant checks ─────────────────────────────────────────────

    def _check_invariants(self, target: LeadStatus) -> None:
        """Enforce domain invariants before a transition is committed."""
        if target == LeadStatus.MATCHING_PROPERTIES:
            if not self.preferred_location:
                raise InvariantViolation(
                    "preferred_location must be set before entering MATCHING_PROPERTIES"
                )
            if self.budget_min is None or self.budget_max is None:
                raise InvariantViolation(
                    "Budget range must be defined before entering MATCHING_PROPERTIES"
                )
