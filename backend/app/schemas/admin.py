"""Admin dashboard request/response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


# ── Property schemas ─────────────────────────────────────────────────


class PropertyCreateRequest(BaseModel):
    location: str
    price: float
    bedrooms: int = 0
    bathrooms: int = 0
    square_feet: int = 0
    available: bool = True


class PropertyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    location: str
    price: float
    bedrooms: int
    bathrooms: int
    square_feet: int
    available: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Lead schemas ─────────────────────────────────────────────────────


class LeadResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    email: str
    phone: str
    budget_min: float | None
    budget_max: float | None
    preferred_location: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    tool_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadDetailResponse(LeadResponse):
    conversation_history: list[ConversationMessageResponse] = []


# ── User admin schemas ───────────────────────────────────────────────


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "AGENT"
