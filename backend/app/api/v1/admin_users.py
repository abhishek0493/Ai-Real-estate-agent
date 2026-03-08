"""Admin API — user management (SUPER_ADMIN only for writes)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_role
from app.models.user import UserModel
from app.schemas.admin import CreateUserRequest
from app.schemas.auth import UserResponse
from app.services.user_management_service import UserManagementService

router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[UserResponse])
async def list_users(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UserResponse]:
    service = UserManagementService(db)
    users = service.list_users(user.tenant_id)
    return [UserResponse.model_validate(u) for u in users]


@router.post("", response_model=UserResponse, status_code=201,
             dependencies=[Depends(require_role("SUPER_ADMIN"))])
async def create_user(
    body: CreateUserRequest,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    service = UserManagementService(db)
    try:
        new_user = service.create_user(
            tenant_id=user.tenant_id,
            email=body.email,
            password=body.password,
            role=body.role,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return UserResponse.model_validate(new_user)


@router.delete("/{user_id}", status_code=204,
               dependencies=[Depends(require_role("SUPER_ADMIN"))])
async def delete_user(
    user_id: UUID,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = UserManagementService(db)
    try:
        service.delete_user(user_id, user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
