"""Lead flow service — orchestrates lead state transitions."""

from __future__ import annotations

from app.domain.entities.lead import Lead, LeadStatus


class LeadFlowService:
    """Domain service that drives a lead through its lifecycle.

    Each method advances the lead exactly one step.  Transition validation
    and invariant enforcement are handled by the Lead entity, which in
    turn delegates to LeadStateMachine.
    """

    def start_collection(self, lead: Lead) -> tuple[LeadStatus, LeadStatus]:
        """INIT → COLLECTING_REQUIREMENTS."""
        return lead.transition_to(LeadStatus.COLLECTING_REQUIREMENTS)

    def validate_budget(self, lead: Lead) -> tuple[LeadStatus, LeadStatus]:
        """COLLECTING_REQUIREMENTS → VALIDATING_BUDGET."""
        return lead.transition_to(LeadStatus.VALIDATING_BUDGET)

    def move_to_matching(self, lead: Lead) -> tuple[LeadStatus, LeadStatus]:
        """VALIDATING_BUDGET → MATCHING_PROPERTIES."""
        return lead.transition_to(LeadStatus.MATCHING_PROPERTIES)

    def start_negotiation(self, lead: Lead) -> tuple[LeadStatus, LeadStatus]:
        """MATCHING_PROPERTIES → NEGOTIATING."""
        return lead.transition_to(LeadStatus.NEGOTIATING)

    def confirm_interest(self, lead: Lead, *, interested: bool) -> tuple[LeadStatus, LeadStatus]:
        """NEGOTIATING → CONFIRMING → INTERESTED or NOT_INTERESTED."""
        lead.transition_to(LeadStatus.CONFIRMING)

        if interested:
            return lead.mark_interested()
        return lead.mark_not_interested()
