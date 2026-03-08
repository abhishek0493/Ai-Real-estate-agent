"""Integration tests for admin property management."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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


PROPERTY_PAYLOAD = {
    "location": "Andheri West",
    "price": 8500000,
    "bedrooms": 2,
    "bathrooms": 1,
    "square_feet": 850,
    "available": True,
}


class TestAdminPropertiesCRUD:
    def test_create_property(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant)
        resp = client.post("/api/v1/admin/properties", json=PROPERTY_PAYLOAD, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["location"] == "Andheri West"
        assert data["price"] == 8500000

    def test_list_properties(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant)
        client.post("/api/v1/admin/properties", json=PROPERTY_PAYLOAD, headers=headers)
        resp = client.get("/api/v1/admin/properties", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_delete_property(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant)
        created = client.post(
            "/api/v1/admin/properties", json=PROPERTY_PAYLOAD, headers=headers,
        ).json()
        resp = client.delete(f"/api/v1/admin/properties/{created['id']}", headers=headers)
        assert resp.status_code == 204


class TestPropertiesRoleRestriction:
    def test_agent_cannot_create(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant, role="AGENT")
        resp = client.post("/api/v1/admin/properties", json=PROPERTY_PAYLOAD, headers=headers)
        assert resp.status_code == 403

    def test_agent_cannot_delete(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant, role="AGENT")
        resp = client.delete(f"/api/v1/admin/properties/{uuid4()}", headers=headers)
        assert resp.status_code == 403

    def test_agent_can_list(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant, role="AGENT")
        resp = client.get("/api/v1/admin/properties", headers=headers)
        assert resp.status_code == 200


class TestPropertiesTenantIsolation:
    def test_cannot_see_other_tenants_properties(
        self, client: TestClient, tenant: TenantModel, other_tenant: TenantModel,
    ) -> None:
        other_headers = _auth_headers(client, other_tenant)
        created = client.post(
            "/api/v1/admin/properties", json=PROPERTY_PAYLOAD, headers=other_headers,
        ).json()

        my_headers = _auth_headers(client, tenant)
        resp = client.get("/api/v1/admin/properties", headers=my_headers)
        ids = [p["id"] for p in resp.json()]
        assert created["id"] not in ids
