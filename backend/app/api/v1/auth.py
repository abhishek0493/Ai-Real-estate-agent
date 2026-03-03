"""API v1 router — authentication."""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])
