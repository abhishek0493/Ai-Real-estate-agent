"""Integration tests for admin user management."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.tenant import TenantModel


def _unique_email() -> str:
    return f"user-{uuid4().hex[:8]}@example.com"


def _auth_headers(client: TestClient, tenant: TenantModel, role: str = "SUPER_ADMIN") -> dict:
    """Register + login a user with the given role, return auth headers."""
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


class TestAdminUsersCRUD:
    def test_list_users(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant)
        resp = client.get("/api/v1/admin/users", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1  # at least the user we just created

    def test_create_user(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant)
        email = _unique_email()
        resp = client.post(
            "/api/v1/admin/users",
            json={"email": email, "password": "NewPass1", "role": "AGENT"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["email"] == email
        assert resp.json()["role"] == "AGENT"

    def test_delete_user(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant)
        email = _unique_email()
        created = client.post(
            "/api/v1/admin/users",
            json={"email": email, "password": "Pass1234", "role": "AGENT"},
            headers=headers,
        ).json()
        resp = client.delete(f"/api/v1/admin/users/{created['id']}", headers=headers)
        assert resp.status_code == 204


class TestAdminUsersRoleRestriction:
    def test_agent_cannot_create_user(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant, role="AGENT")
        resp = client.post(
            "/api/v1/admin/users",
            json={"email": _unique_email(), "password": "Pass1234", "role": "AGENT"},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_agent_cannot_delete_user(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant, role="AGENT")
        resp = client.delete(f"/api/v1/admin/users/{uuid4()}", headers=headers)
        assert resp.status_code == 403

    def test_agent_can_list_users(self, client: TestClient, tenant: TenantModel) -> None:
        headers = _auth_headers(client, tenant, role="AGENT")
        resp = client.get("/api/v1/admin/users", headers=headers)
        assert resp.status_code == 200


class TestAdminUsersTenantIsolation:
    def test_cannot_see_other_tenants_users(
        self, client: TestClient, tenant: TenantModel, other_tenant: TenantModel,
    ) -> None:
        # Create user in other_tenant
        other_headers = _auth_headers(client, other_tenant)
        email = _unique_email()
        client.post(
            "/api/v1/admin/users",
            json={"email": email, "password": "Pass1234", "role": "AGENT"},
            headers=other_headers,
        )

        # List users with tenant — should not include other_tenant's user
        my_headers = _auth_headers(client, tenant)
        resp = client.get("/api/v1/admin/users", headers=my_headers)
        emails = [u["email"] for u in resp.json()]
        assert email not in emails
