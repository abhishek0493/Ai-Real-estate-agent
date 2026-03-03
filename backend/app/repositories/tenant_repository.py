"""Tenant repository — all queries scoped by tenant identity."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import TenantModel


class TenantRepository:
    """Concrete repository for Tenant data access."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_api_key(self, api_key: str) -> TenantModel | None:
        stmt = select(TenantModel).where(
            TenantModel.api_key == api_key,
            TenantModel.is_active.is_(True),
        )
        return self._db.scalars(stmt).first()

    def get_by_id(self, tenant_id: UUID) -> TenantModel | None:
        return self._db.get(TenantModel, tenant_id)

    def create(self, tenant: TenantModel) -> TenantModel:
        self._db.add(tenant)
        self._db.commit()
        self._db.refresh(tenant)
        return tenant
