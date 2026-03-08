"""API v1 router — authentication (register, login, me)."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.tenant import get_current_tenant
from app.models.tenant import TenantModel
from app.models.user import UserModel
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    tenant: Annotated[TenantModel, Depends(get_current_tenant)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserResponse:
    """Register a new dashboard user under the resolved tenant."""
    service = AuthService(
        db=db,
        secret_key=settings.SECRET_KEY,
        token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    try:
        user = service.register_user(
            tenant_id=tenant.id,
            email=body.email,
            password=body.password,
            role=body.role,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    tenant: Annotated[TenantModel, Depends(get_current_tenant)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Authenticate a user and return a JWT access token."""
    service = AuthService(
        db=db,
        secret_key=settings.SECRET_KEY,
        token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    try:
        user = service.authenticate_user(
            tenant_id=tenant.id,
            email=body.email,
            password=body.password,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = service.generate_token(user)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(
    user: Annotated[UserModel, Depends(get_current_user)],
) -> UserResponse:
    """Return the currently authenticated user's info."""
    return UserResponse.model_validate(user)
