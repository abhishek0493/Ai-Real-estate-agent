"""Tenant provisioning service — creates tenants, seeds properties and prompts."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import generate_api_key
from app.models.lead import LeadModel
from app.models.prompt_version import PromptVersionModel
from app.models.property import PropertyModel
from app.models.tenant import TenantModel

logger = logging.getLogger(__name__)

# Realistic Mumbai properties for seeding
_SEED_PROPERTIES = [
    {"location": "Andheri West", "price": 8_500_000, "bedrooms": 2, "bathrooms": 2, "square_feet": 850},
    {"location": "Andheri East", "price": 7_200_000, "bedrooms": 2, "bathrooms": 1, "square_feet": 750},
    {"location": "Bandra West", "price": 25_000_000, "bedrooms": 3, "bathrooms": 3, "square_feet": 1400},
    {"location": "Bandra East", "price": 15_000_000, "bedrooms": 3, "bathrooms": 2, "square_feet": 1200},
    {"location": "Powai", "price": 12_000_000, "bedrooms": 2, "bathrooms": 2, "square_feet": 1050},
    {"location": "Worli", "price": 35_000_000, "bedrooms": 3, "bathrooms": 3, "square_feet": 1600},
    {"location": "Juhu", "price": 30_000_000, "bedrooms": 4, "bathrooms": 3, "square_feet": 1800},
    {"location": "Goregaon West", "price": 6_500_000, "bedrooms": 1, "bathrooms": 1, "square_feet": 550},
    {"location": "Malad West", "price": 5_800_000, "bedrooms": 1, "bathrooms": 1, "square_feet": 500},
    {"location": "Thane West", "price": 4_500_000, "bedrooms": 2, "bathrooms": 1, "square_feet": 700},
]


class TenantProvisioningService:
    """Handles tenant creation, property seeding, and prompt version setup."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create_tenant(self, name: str, email: str) -> TenantModel:
        """Create a tenant or return existing one (idempotent).

        If a tenant with the same name already exists, returns it without
        modification.  Otherwise creates a new tenant with a generated API key.
        """
        existing = self._db.scalars(
            select(TenantModel).where(TenantModel.name == name)
        ).first()

        if existing is not None:
            logger.info("Tenant '%s' already exists (id=%s)", name, existing.id)
            return existing

        tenant = TenantModel(
            name=name,
            api_key=generate_api_key(),
            is_active=True,
        )
        self._db.add(tenant)
        self._db.flush()
        logger.info("Created tenant '%s' (id=%s)", name, tenant.id)
        return tenant

    def seed_properties(self, tenant: TenantModel) -> int:
        """Seed demo properties for a tenant. Skips if properties already exist.

        Returns the number of properties created.
        """
        count = self._db.scalars(
            select(PropertyModel.id).where(PropertyModel.tenant_id == tenant.id).limit(1)
        ).first()

        if count is not None:
            logger.info("Tenant '%s' already has properties — skipping seed", tenant.name)
            return 0

        for prop_data in _SEED_PROPERTIES:
            self._db.add(PropertyModel(tenant_id=tenant.id, available=True, **prop_data))

        self._db.flush()
        logger.info("Seeded %d properties for tenant '%s'", len(_SEED_PROPERTIES), tenant.name)
        return len(_SEED_PROPERTIES)

    def seed_prompt_version(self) -> PromptVersionModel:
        """Ensure the default 'v1' prompt version exists (idempotent)."""
        existing = self._db.scalars(
            select(PromptVersionModel).where(PromptVersionModel.version_name == "v1")
        ).first()

        if existing is not None:
            logger.info("Prompt version 'v1' already exists")
            return existing

        pv = PromptVersionModel(
            version_name="v1",
            description="Initial production prompt for real estate assistant",
            is_active=True,
        )
        self._db.add(pv)
        self._db.flush()
        logger.info("Created prompt version 'v1'")
        return pv

    def provision_full(self, name: str, email: str) -> TenantModel:
        """Full provisioning: create tenant + seed properties + seed prompt.

        Wraps everything in a single transaction.
        """
        tenant = self.create_tenant(name, email)
        self.seed_properties(tenant)
        self.seed_prompt_version()
        self._db.commit()
        return tenant
