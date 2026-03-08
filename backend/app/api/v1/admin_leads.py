"""Admin API — leads view (read-only, all roles)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import UserModel
from app.schemas.admin import (
    ConversationMessageResponse,
    LeadDetailResponse,
    LeadResponse,
)
from app.services.lead_management_service import LeadManagementService

router = APIRouter(
    prefix="/admin/leads",
    tags=["admin-leads"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[LeadResponse]:
    service = LeadManagementService(db)
    leads = service.list_leads(user.tenant_id)
    return [LeadResponse.model_validate(l) for l in leads]


@router.get("/{lead_id}", response_model=LeadDetailResponse)
async def get_lead_detail(
    lead_id: UUID,
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LeadDetailResponse:
    service = LeadManagementService(db)
    try:
        lead, history = service.get_lead_detail(lead_id, user.tenant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return LeadDetailResponse(
        **LeadResponse.model_validate(lead).model_dump(),
        conversation_history=[
            ConversationMessageResponse.model_validate(m) for m in history
        ],
    )
