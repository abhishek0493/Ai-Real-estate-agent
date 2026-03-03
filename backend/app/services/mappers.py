"""Domain ↔ DB mapping functions for Lead."""

from __future__ import annotations

from uuid import UUID

from app.domain.entities.lead import Lead, LeadId, LeadStatus
from app.models.lead import LeadModel


def model_to_domain(model: LeadModel) -> Lead:
    """Convert a SQLAlchemy LeadModel to a domain Lead entity."""
    return Lead(
        id=LeadId(model.id),
        tenant_id=model.tenant_id,
        name=model.name,
        email=model.email,
        phone=model.phone,
        budget_min=model.budget_min,
        budget_max=model.budget_max,
        preferred_location=model.preferred_location,
        status=LeadStatus(model.status),
    )


def domain_to_model(lead: Lead, *, existing: LeadModel | None = None) -> LeadModel:
    """Apply domain Lead state onto a SQLAlchemy model.

    If *existing* is provided, update it in place (for persistence).
    Otherwise create a new LeadModel.
    """
    if existing is not None:
        existing.name = lead.name
        existing.email = lead.email
        existing.phone = lead.phone
        existing.budget_min = lead.budget_min
        existing.budget_max = lead.budget_max
        existing.preferred_location = lead.preferred_location
        existing.status = lead.status.value
        return existing

    return LeadModel(
        id=UUID(str(lead.id)),
        tenant_id=lead.tenant_id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        budget_min=lead.budget_min,
        budget_max=lead.budget_max,
        preferred_location=lead.preferred_location,
        status=lead.status.value,
    )
