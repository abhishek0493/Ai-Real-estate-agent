"""API v1 router — admin leads and properties (protected by JWT)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.user import UserModel

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/dashboard")
async def dashboard(
    user: Annotated[UserModel, Depends(get_current_user)],
) -> dict:
    """Protected dashboard endpoint — requires valid JWT."""
    return {
        "message": f"Welcome, {user.email}",
        "tenant_id": str(user.tenant_id),
        "role": user.role,
    }
