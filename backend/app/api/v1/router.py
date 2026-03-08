"""API v1 aggregated router."""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.admin_leads import router as admin_leads_router
from app.api.v1.admin_properties import router as admin_properties_router
from app.api.v1.admin_users import router as admin_users_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.tenants import router as tenants_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(chat_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(tenants_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(admin_users_router)
api_v1_router.include_router(admin_properties_router)
api_v1_router.include_router(admin_leads_router)
