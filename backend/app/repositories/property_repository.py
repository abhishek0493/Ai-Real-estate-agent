"""Property repository — all queries scoped by tenant_id."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.property import PropertyModel


class PropertyRepository:
    """Concrete repository for Property data access. Tenant-scoped."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, property_id: UUID, tenant_id: UUID) -> PropertyModel | None:
        stmt = select(PropertyModel).where(
            PropertyModel.id == property_id,
            PropertyModel.tenant_id == tenant_id,
        )
        return self._db.scalars(stmt).first()

    def list_by_tenant(
        self, tenant_id: UUID, *, skip: int = 0, limit: int = 100
    ) -> list[PropertyModel]:
        stmt = (
            select(PropertyModel)
            .where(PropertyModel.tenant_id == tenant_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.scalars(stmt).all())

    def create(self, prop: PropertyModel) -> PropertyModel:
        self._db.add(prop)
        self._db.commit()
        self._db.refresh(prop)
        return prop
