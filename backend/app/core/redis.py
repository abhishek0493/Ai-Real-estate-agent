"""Redis client setup."""

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
