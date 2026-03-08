"""Property management service — tenant-scoped CRUD."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.property import PropertyModel
from app.repositories.property_repository import PropertyRepository

logger = logging.getLogger(__name__)


class PropertyManagementService:
    """CRUD operations for tenant properties."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = PropertyRepository(db)

    def list_properties(self, tenant_id: UUID) -> list[PropertyModel]:
        return self._repo.list_by_tenant(tenant_id)

    def create_property(
        self,
        tenant_id: UUID,
        location: str,
        price: float,
        bedrooms: int = 0,
        bathrooms: int = 0,
        square_feet: int = 0,
        available: bool = True,
    ) -> PropertyModel:
        prop = PropertyModel(
            tenant_id=tenant_id,
            location=location,
            price=price,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=square_feet,
            available=available,
        )
        self._repo.create(prop)
        logger.info("Created property in '%s' for tenant %s", location, tenant_id)
        return prop

    def delete_property(self, property_id: UUID, tenant_id: UUID) -> None:
        prop = self._repo.get_by_id(property_id, tenant_id)
        if prop is None:
            raise ValueError("Property not found")
        self._db.delete(prop)
        self._db.commit()
        logger.info("Deleted property %s from tenant %s", property_id, tenant_id)
