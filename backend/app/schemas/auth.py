"""Auth request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """User registration payload."""

    email: EmailStr
    password: str
    role: str = "AGENT"


class LoginRequest(BaseModel):
    """User login payload."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user info — never exposes hashed_password."""

    id: UUID
    tenant_id: UUID
    email: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
