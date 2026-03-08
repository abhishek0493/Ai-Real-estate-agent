"""Chat service — application layer orchestrating AI + persistence."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.llm.base import LLMClient
from app.ai.orchestrator.engine import AIOrchestrator
from app.ai.tools import build_default_registry
from app.models.conversation import ConversationMessageModel
from app.models.lead import LeadModel
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.lead_repository import LeadRepository
from app.services.mappers import domain_to_model, model_to_domain

logger = logging.getLogger(__name__)


class ChatService:
    """Application-layer service that wires AI orchestration with persistence.

    The route handler is kept thin — all coordination lives here.
    """

    def __init__(self, db: Session, llm_client: LLMClient) -> None:
        self._db = db
        self._lead_repo = LeadRepository(db)
        self._conv_repo = ConversationRepository(db)
        self._orchestrator = AIOrchestrator(
            llm_client=llm_client,
            registry=build_default_registry(db=db),
        )

    async def handle_message(
        self,
        tenant_id: UUID,
        user_message: str,
        lead_id: UUID | None = None,
    ) -> dict:
        """Process a chat message: resolve lead, call AI, persist everything.

        Returns a dict matching the ChatResponse schema fields.
        """
        # 1. Resolve or create lead
        lead_model = self._resolve_lead(tenant_id, lead_id)

        # 2. Load conversation history
        history = self._load_history(lead_model.id, tenant_id)

        # 3. Convert DB model → domain entity
        domain_lead = model_to_domain(lead_model)

        # 4. Call AI orchestrator
        ai_response = await self._orchestrator.process_message(
            lead=domain_lead,
            user_message=user_message,
            conversation_history=history,
        )

        # 5. Apply domain changes back to the DB model
        domain_to_model(domain_lead, existing=lead_model)

        # 6. Persist conversation messages
        self._persist_messages(
            tenant_id=tenant_id,
            lead_id=lead_model.id,
            user_message=user_message,
            assistant_message=ai_response.assistant_message,
            tool_name=ai_response.executed_tool,
        )

        # 7. Commit the transaction
        self._db.commit()

        return {
            "assistant_message": ai_response.assistant_message,
            "lead_id": lead_model.id,
            "current_status": domain_lead.status.value,
            "tool_executed": ai_response.executed_tool,
            "error": ai_response.error,
        }

    # ── Private helpers ──────────────────────────────────────────────

    def _resolve_lead(self, tenant_id: UUID, lead_id: UUID | None) -> LeadModel:
        if lead_id is not None:
            model = self._lead_repo.get_by_id(lead_id, tenant_id)
            if model is None:
                raise ValueError(f"Lead {lead_id} not found for this tenant")
            return model

        # Create a new lead in INIT state
        new_lead = LeadModel(tenant_id=tenant_id, name="Anonymous", email="", status="INIT")
        self._db.add(new_lead)
        self._db.flush()
        return new_lead

    def _load_history(
        self, lead_id: UUID, tenant_id: UUID
    ) -> list[dict[str, str]]:
        messages = self._conv_repo.get_history(lead_id, tenant_id, limit=20)
        return [{"role": m.role, "content": m.content} for m in messages]

    def _persist_messages(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        user_message: str,
        assistant_message: str,
        tool_name: str | None,
    ) -> None:
        self._conv_repo.add_message(
            ConversationMessageModel(
                tenant_id=tenant_id,
                lead_id=lead_id,
                role="user",
                content=user_message,
            )
        )
        self._conv_repo.add_message(
            ConversationMessageModel(
                tenant_id=tenant_id,
                lead_id=lead_id,
                role="assistant",
                content=assistant_message,
                tool_name=tool_name,
            )
        )
