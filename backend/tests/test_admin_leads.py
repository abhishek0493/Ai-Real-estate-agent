"""Integration tests for admin leads view."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.lead import LeadModel
from app.models.tenant import TenantModel


def _unique_email() -> str:
    return f"user-{uuid4().hex[:8]}@example.com"


def _auth_headers(client: TestClient, tenant: TenantModel, role: str = "SUPER_ADMIN") -> dict:
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Pass1234", "role": role},
        headers={"X-Tenant-Key": tenant.api_key},
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Pass1234"},
        headers={"X-Tenant-Key": tenant.api_key},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_lead(db: Session, tenant: TenantModel) -> LeadModel:
    lead = LeadModel(
        tenant_id=tenant.id,
        name="Test Lead",
        email="lead@example.com",
        status="INIT",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


class TestAdminLeads:
    def test_list_leads(self, client: TestClient, tenant: TenantModel, db: Session) -> None:
        _create_lead(db, tenant)
        headers = _auth_headers(client, tenant)
        resp = client.get("/api/v1/admin/leads", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_lead_detail(self, client: TestClient, tenant: TenantModel, db: Session) -> None:
        lead = _create_lead(db, tenant)
        headers = _auth_headers(client, tenant)
        resp = client.get(f"/api/v1/admin/leads/{lead.id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(lead.id)
        assert "conversation_history" in data

    def test_lead_not_found(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant)
        resp = client.get(f"/api/v1/admin/leads/{uuid4()}", headers=headers)
        assert resp.status_code == 404

    def test_agent_can_list_leads(self, client: TestClient, tenant: TenantModel, db: Session) -> None:
        _create_lead(db, tenant)
        headers = _auth_headers(client, tenant, role="AGENT")
        resp = client.get("/api/v1/admin/leads", headers=headers)
        assert resp.status_code == 200


class TestLeadsTenantIsolation:
    def test_cannot_see_other_tenants_leads(
        self, client: TestClient, tenant: TenantModel, other_tenant: TenantModel, db: Session,
    ) -> None:
        lead = _create_lead(db, other_tenant)
        my_headers = _auth_headers(client, tenant)
        resp = client.get(f"/api/v1/admin/leads/{lead.id}", headers=my_headers)
        assert resp.status_code == 404
