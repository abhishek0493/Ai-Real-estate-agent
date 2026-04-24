"""Tenant request/response schemas."""

from uuid import UUID
from pydantic import BaseModel, EmailStr


class TenantCreateRequest(BaseModel):
    name: str
    email: EmailStr
    secret_key: str


class TenantResponse(BaseModel):
    id: UUID
    name: str
    api_key: str

    model_config = {"from_attributes": True}
