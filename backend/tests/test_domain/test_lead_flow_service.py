"""Tests for LeadFlowService orchestration."""

from uuid import uuid4

import pytest

from app.domain.entities.lead import Lead, LeadStatus
from app.domain.exceptions import InvariantViolation, InvalidStateTransition
from app.domain.services.lead_flow_service import LeadFlowService


@pytest.fixture
def service() -> LeadFlowService:
    return LeadFlowService()


@pytest.fixture
def lead() -> Lead:
    return Lead(
        tenant_id=uuid4(),
        name="Bob",
        email="bob@example.com",
        budget_min=100_000,
        budget_max=300_000,
        preferred_location="Mumbai",
    )


class TestHappyPath:
    """Walk the full lifecycle through the service."""

    def test_full_interested_flow(self, service: LeadFlowService, lead: Lead) -> None:
        prev, new = service.start_collection(lead)
        assert prev == LeadStatus.INIT
        assert new == LeadStatus.COLLECTING_REQUIREMENTS

        service.validate_budget(lead)
        assert lead.status == LeadStatus.VALIDATING_BUDGET

        service.move_to_matching(lead)
        assert lead.status == LeadStatus.MATCHING_PROPERTIES

        service.start_negotiation(lead)
        assert lead.status == LeadStatus.NEGOTIATING

        prev, new = service.confirm_interest(lead, interested=True)
        assert prev == LeadStatus.CONFIRMING
        assert new == LeadStatus.INTERESTED

    def test_full_not_interested_flow(self, service: LeadFlowService, lead: Lead) -> None:
        service.start_collection(lead)
        service.validate_budget(lead)
        service.move_to_matching(lead)
        service.start_negotiation(lead)
        service.confirm_interest(lead, interested=False)
        assert lead.status == LeadStatus.NOT_INTERESTED

    def test_service_returns_tuples(self, service: LeadFlowService, lead: Lead) -> None:
        result = service.start_collection(lead)
        assert isinstance(result, tuple) and len(result) == 2


class TestInvalidFlows:
    def test_validate_budget_from_init_raises(self, service: LeadFlowService, lead: Lead) -> None:
        with pytest.raises(InvalidStateTransition):
            service.validate_budget(lead)

    def test_start_negotiation_from_init_raises(self, service: LeadFlowService, lead: Lead) -> None:
        with pytest.raises(InvalidStateTransition):
            service.start_negotiation(lead)

    def test_confirm_interest_from_init_raises(self, service: LeadFlowService, lead: Lead) -> None:
        with pytest.raises(InvalidStateTransition):
            service.confirm_interest(lead, interested=True)

    def test_double_collection_raises(self, service: LeadFlowService, lead: Lead) -> None:
        service.start_collection(lead)
        with pytest.raises(InvalidStateTransition):
            service.start_collection(lead)


class TestInvariantEnforcement:
    def test_move_to_matching_without_location_raises(self, service: LeadFlowService) -> None:
        lead = Lead(
            tenant_id=uuid4(),
            name="Eve",
            email="eve@example.com",
            budget_min=100_000,
            budget_max=200_000,
            preferred_location="",
        )
        service.start_collection(lead)
        service.validate_budget(lead)
        with pytest.raises(InvariantViolation, match="preferred_location"):
            service.move_to_matching(lead)

    def test_move_to_matching_without_budget_raises(self, service: LeadFlowService) -> None:
        lead = Lead(
            tenant_id=uuid4(),
            name="Eve",
            email="eve@example.com",
            preferred_location="Delhi",
        )
        service.start_collection(lead)
        service.validate_budget(lead)
        with pytest.raises(InvariantViolation, match="Budget range"):
            service.move_to_matching(lead)
