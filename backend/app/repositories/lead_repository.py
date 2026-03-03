"""Lead repository — all queries scoped by tenant_id."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lead import LeadModel


class LeadRepository:
    """Concrete repository for Lead data access. Every query is tenant-scoped."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, lead_id: UUID, tenant_id: UUID) -> LeadModel | None:
        stmt = select(LeadModel).where(
            LeadModel.id == lead_id,
            LeadModel.tenant_id == tenant_id,
        )
        return self._db.scalars(stmt).first()

    def list_by_tenant(
        self, tenant_id: UUID, *, skip: int = 0, limit: int = 100
    ) -> list[LeadModel]:
        stmt = (
            select(LeadModel)
            .where(LeadModel.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.scalars(stmt).all())

    def create(self, lead: LeadModel) -> LeadModel:
        self._db.add(lead)
        self._db.commit()
        self._db.refresh(lead)
        return lead

    def update(self, lead: LeadModel) -> LeadModel:
        self._db.commit()
        self._db.refresh(lead)
        return lead
