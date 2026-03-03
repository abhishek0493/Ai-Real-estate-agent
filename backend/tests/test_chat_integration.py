"""Integration tests for /api/v1/chat endpoint."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.llm.base import LLMResponse, ToolCallResult
from app.models.lead import LeadModel
from app.models.tenant import TenantModel

from tests.conftest import MockLLMClient


# ── Helpers ──────────────────────────────────────────────────────────


def _patch_llm(response: LLMResponse):
    """Patch OpenAIClient so the chat endpoint uses our mock."""
    mock = MockLLMClient(response)
    return patch("app.api.v1.chat.OpenAIClient", return_value=mock)


def _make_lead(db: Session, tenant: TenantModel, **overrides: Any) -> LeadModel:
    defaults = {
        "tenant_id": tenant.id,
        "name": "Alice",
        "email": "alice@example.com",
        "status": "INIT",
    }
    lead = LeadModel(**(defaults | overrides))
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


# ── Tests ────────────────────────────────────────────────────────────


class TestNewLeadConversation:
    def test_creates_lead_on_first_message(
        self, client: TestClient, tenant: TenantModel
    ) -> None:
        with _patch_llm(LLMResponse(message="Hello! How can I help?")):
            resp = client.post(
                "/api/v1/chat",
                json={"message": "Hi"},
                headers={"X-Tenant-Key": tenant.api_key},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["assistant_message"] == "Hello! How can I help?"
        assert data["lead_id"] is not None
        assert data["current_status"] == "INIT"


class TestExistingLeadFlow:
    def test_resume_existing_lead(
        self, client: TestClient, tenant: TenantModel, db: Session
    ) -> None:
        lead = _make_lead(db, tenant)

        with _patch_llm(
            LLMResponse(
                message="Starting collection.",
                tool_call=ToolCallResult(name="start_collection", arguments={}),
            )
        ):
            resp = client.post(
                "/api/v1/chat",
                json={"message": "I want a house", "lead_id": str(lead.id)},
                headers={"X-Tenant-Key": tenant.api_key},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["current_status"] == "COLLECTING_REQUIREMENTS"
        assert data["tool_executed"] == "start_collection"


class TestToolExecutionPersists:
    def test_budget_update_persisted(
        self, client: TestClient, tenant: TenantModel, db: Session
    ) -> None:
        lead = _make_lead(db, tenant, status="COLLECTING_REQUIREMENTS")

        with _patch_llm(
            LLMResponse(
                message="Got it.",
                tool_call=ToolCallResult(
                    name="update_budget",
                    arguments={"budget_min": 100_000, "budget_max": 250_000},
                ),
            )
        ):
            resp = client.post(
                "/api/v1/chat",
                json={"message": "budget 100k-250k", "lead_id": str(lead.id)},
                headers={"X-Tenant-Key": tenant.api_key},
            )
        assert resp.status_code == 200

        # Verify persisted in DB
        db.refresh(lead)
        assert lead.budget_min == 100_000
        assert lead.budget_max == 250_000


class TestTenantIsolation:
    def test_cannot_access_other_tenants_lead(
        self,
        client: TestClient,
        tenant: TenantModel,
        other_tenant: TenantModel,
        db: Session,
    ) -> None:
        # Create lead under other_tenant
        other_lead = _make_lead(db, other_tenant, name="Eve")

        # Try to access it with tenant's key
        with _patch_llm(LLMResponse(message="Hi")):
            resp = client.post(
                "/api/v1/chat",
                json={"message": "Hi", "lead_id": str(other_lead.id)},
                headers={"X-Tenant-Key": tenant.api_key},
            )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestInvalidApiKey:
    def test_missing_key_returns_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/chat", json={"message": "Hi"})
        assert resp.status_code == 422

    def test_wrong_key_returns_401(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/chat",
            json={"message": "Hi"},
            headers={"X-Tenant-Key": "invalid-key"},
        )
        assert resp.status_code == 401
