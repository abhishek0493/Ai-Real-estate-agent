"""Tenant resolution dependency — resolves tenant from X-Tenant-Key header."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tenant import TenantModel
from app.repositories.tenant_repository import TenantRepository


async def get_current_tenant(
    x_tenant_key: Annotated[str, Header()],
    db: Annotated[Session, Depends(get_db)],
) -> TenantModel:
    """FastAPI dependency — resolve the active tenant from the API key header.

    Raises HTTP 401 if the key is missing/invalid or the tenant is inactive.
    """
    repo = TenantRepository(db)
    tenant = repo.get_by_api_key(x_tenant_key)
    if tenant is None:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    return tenant
