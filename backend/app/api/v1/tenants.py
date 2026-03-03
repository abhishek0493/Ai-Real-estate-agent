"""API v1 router — tenant registration."""

from fastapi import APIRouter

router = APIRouter(prefix="/tenants", tags=["tenants"])
