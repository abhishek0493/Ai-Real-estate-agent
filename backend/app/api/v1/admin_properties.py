"""Admin API — property management (SUPER_ADMIN only for writes)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import require_role
from app.models.user import UserModel
from app.schemas.admin import PropertyCreateRequest, PropertyResponse
from app.services.property_management_service import PropertyManagementService

router = APIRouter(
    prefix="/admin/properties",
    tags=["admin-properties"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[PropertyResponse])
async def list_properties(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[PropertyResponse]:
    service = PropertyManagementService(db)
    props = service.list_properties(user.tenant_id)
    return [PropertyResponse.model_validate(p) for p in props]


@router.post("", response_model=PropertyResponse, status_code=201,
             dependencies=[Depends(require_role("SUPER_ADMIN"))])
async def create_property(
    body: PropertyCreateRequest,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PropertyResponse:
    service = PropertyManagementService(db)
    prop = service.create_property(
        tenant_id=user.tenant_id,
        location=body.location,
        price=body.price,
        bedrooms=body.bedrooms,
        bathrooms=body.bathrooms,
        square_feet=body.square_feet,
        available=body.available,
    )
    return PropertyResponse.model_validate(prop)


@router.delete("/{property_id}", status_code=204,
               dependencies=[Depends(require_role("SUPER_ADMIN"))])
async def delete_property(
    property_id: UUID,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = PropertyManagementService(db)
    try:
        service.delete_property(property_id, user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
