"""Lead management service — read-only tenant-scoped access."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.conversation import ConversationMessageModel
from app.models.lead import LeadModel
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.lead_repository import LeadRepository


class LeadManagementService:
    """Read-only access to tenant leads and conversations."""

    def __init__(self, db: Session) -> None:
        self._lead_repo = LeadRepository(db)
        self._conv_repo = ConversationRepository(db)

    def list_leads(self, tenant_id: UUID) -> list[LeadModel]:
        return self._lead_repo.list_by_tenant(tenant_id)

    def get_lead_detail(
        self, lead_id: UUID, tenant_id: UUID,
    ) -> tuple[LeadModel, list[ConversationMessageModel]]:
        """Return a lead and its conversation history.

        Raises ``ValueError`` if the lead doesn't exist or belongs to another tenant.
        """
        lead = self._lead_repo.get_by_id(lead_id, tenant_id)
        if lead is None:
            raise ValueError("Lead not found")

        history = self._conv_repo.get_history(lead_id, tenant_id, limit=100)
        return lead, history
