"""API v1 router — tenant registration."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.tenant import TenantCreateRequest, TenantResponse
from app.services.tenant_provisioning_service import TenantProvisioningService

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("/generate", response_model=TenantResponse, status_code=201)
async def generate_tenant(
    body: TenantCreateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> TenantResponse:
    """Generate a new tenant using the super admin secret key."""
    if not settings.SUPER_ADMIN_TENANT_GENERATE_KEY:
        raise HTTPException(
            status_code=500, detail="Tenant generation is disabled. Secret key not configured."
        )

    if body.secret_key != settings.SUPER_ADMIN_TENANT_GENERATE_KEY:
        raise HTTPException(status_code=403, detail="Invalid secret key.")

    service = TenantProvisioningService(db)
    tenant = service.provision_full(name=body.name, email=body.email)
    
    return TenantResponse.model_validate(tenant)
