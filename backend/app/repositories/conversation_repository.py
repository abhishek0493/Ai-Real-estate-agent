"""Conversation repository — all queries scoped by tenant_id."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import ConversationMessageModel


class ConversationRepository:
    """Concrete repository for conversation messages. Tenant-scoped."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_history(
        self, lead_id: UUID, tenant_id: UUID, *, limit: int = 20
    ) -> list[ConversationMessageModel]:
        stmt = (
            select(ConversationMessageModel)
            .where(
                ConversationMessageModel.lead_id == lead_id,
                ConversationMessageModel.tenant_id == tenant_id,
            )
            .order_by(ConversationMessageModel.created_at.desc())
            .limit(limit)
        )
        rows = list(self._db.scalars(stmt).all())
        rows.reverse()  # oldest first
        return rows

    def add_message(self, message: ConversationMessageModel) -> ConversationMessageModel:
        self._db.add(message)
        self._db.flush()  # flush (not commit) — caller owns the transaction
        return message
