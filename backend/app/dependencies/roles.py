"""Role-based access control dependency."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.user import UserModel


def require_role(*allowed_roles: str):
    """Return a FastAPI dependency that enforces role-based access.

    Usage::

        @router.post("/admin/users", dependencies=[Depends(require_role("SUPER_ADMIN"))])
        async def create_user(...): ...
    """

    async def _check_role(
        user: Annotated[UserModel, Depends(get_current_user)],
    ) -> UserModel:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )
        return user

    return _check_role
