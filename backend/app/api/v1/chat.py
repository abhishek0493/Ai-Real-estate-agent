"""API v1 router — chat endpoint."""

from __future__ import annotations

import logging
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.llm.openai_client import OpenAIClient
from app.core.config import Settings, get_settings
from app.core.redis import get_redis
from app.db.session import get_db
from app.dependencies.tenant import get_current_tenant
from app.models.tenant import TenantModel
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    tenant: Annotated[TenantModel, Depends(get_current_tenant)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> ChatResponse:
    """Process a user message through the AI pipeline.

    Thin controller — all logic lives in ChatService.
    """
    llm_client = OpenAIClient(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
    service = ChatService(db=db, llm_client=llm_client, redis_client=redis)

    try:
        result = await service.handle_message(
            tenant_id=tenant.id,
            user_message=body.message,
            lead_id=body.lead_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ChatResponse(**result)
