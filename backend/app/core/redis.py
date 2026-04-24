"""Redis client setup."""

from __future__ import annotations

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends

from app.core.config import Settings, get_settings

_redis_client: aioredis.Redis | None = None


async def get_redis(
    settings: Annotated[Settings, Depends(get_settings)],
) -> aioredis.Redis:
    """FastAPI dependency — returns a shared async Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


async def get_redis_client(redis_url: str | None = None) -> aioredis.Redis:
    """Return the shared Redis client without FastAPI Depends.

    Use this in service-layer code (ChatService, StateManager, etc.)
    where FastAPI's DI is not available.  Falls back to settings if
    *redis_url* is not provided.
    """
    global _redis_client
    if _redis_client is None:
        url = redis_url or get_settings().REDIS_URL
        _redis_client = aioredis.from_url(url, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    """Gracefully close the Redis connection pool.

    Call this during application shutdown.
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
