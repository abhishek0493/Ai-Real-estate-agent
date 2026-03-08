"""Integration tests for JWT authentication — register, login, me, and protection."""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.tenant import TenantModel


_settings = get_settings()


def _unique_email() -> str:
    """Generate a unique email per test invocation."""
    return f"user-{uuid4().hex[:8]}@example.com"


def _register(client: TestClient, tenant: TenantModel, email: str, password: str = "StrongP@ss1"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
        headers={"X-Tenant-Key": tenant.api_key},
    )


def _login(client: TestClient, tenant: TenantModel, email: str, password: str = "StrongP@ss1"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"X-Tenant-Key": tenant.api_key},
    )


# ── Registration ─────────────────────────────────────────────────────


class TestRegister:
    def test_register_success(self, client: TestClient, tenant: TenantModel) -> None:
        email = _unique_email()
        resp = _register(client, tenant, email)
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == email
        assert data["tenant_id"] == str(tenant.id)
        assert "hashed_password" not in data

    def test_duplicate_email_returns_409(self, client: TestClient, tenant: TenantModel) -> None:
        email = _unique_email()
        _register(client, tenant, email)
        resp = _register(client, tenant, email)
        assert resp.status_code == 409


# ── Login ────────────────────────────────────────────────────────────


class TestLogin:
    def test_login_success(self, client: TestClient, tenant: TenantModel) -> None:
        email = _unique_email()
        _register(client, tenant, email)
        resp = _login(client, tenant, email)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client: TestClient, tenant: TenantModel) -> None:
        email = _unique_email()
        _register(client, tenant, email)
        resp = _login(client, tenant, email, password="WrongPass")
        assert resp.status_code == 401

    def test_nonexistent_user_returns_401(self, client: TestClient, tenant: TenantModel) -> None:
        resp = _login(client, tenant, _unique_email())
        assert resp.status_code == 401


# ── /auth/me ─────────────────────────────────────────────────────────


class TestMe:
    def test_me_with_valid_token(self, client: TestClient, tenant: TenantModel) -> None:
        email = _unique_email()
        _register(client, tenant, email)
        token = _login(client, tenant, email).json()["access_token"]

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == email
        assert data["tenant_id"] == str(tenant.id)

    def test_me_without_token_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/auth/me")
        # HTTPBearer returns 403 when not provided
        assert resp.status_code in (401, 403)

    def test_me_with_invalid_token_returns_401(self, client: TestClient) -> None:
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


# ── Expired token ────────────────────────────────────────────────────


class TestExpiredToken:
    def test_expired_token_returns_401(self, client: TestClient, tenant: TenantModel) -> None:
        token = create_access_token(
            data={"sub": str(uuid4()), "tenant_id": str(tenant.id)},
            secret_key=_settings.SECRET_KEY,
            expires_delta=timedelta(seconds=-1),
        )
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


# ── Cross-tenant protection ─────────────────────────────────────────


class TestCrossTenant:
    def test_cannot_login_to_wrong_tenant(
        self, client: TestClient, tenant: TenantModel, other_tenant: TenantModel,
    ) -> None:
        email = _unique_email()
        _register(client, tenant, email)
        resp = _login(client, other_tenant, email)
        assert resp.status_code == 401


# ── Admin protected routes ───────────────────────────────────────────


class TestAdminProtection:
    def test_admin_without_token_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/v1/admin/dashboard")
        assert resp.status_code in (401, 403)

    def test_admin_with_valid_token(self, client: TestClient, tenant: TenantModel) -> None:
        email = _unique_email()
        _register(client, tenant, email)
        token = _login(client, tenant, email).json()["access_token"]

        resp = client.get(
            "/api/v1/admin/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"].startswith("Welcome")
