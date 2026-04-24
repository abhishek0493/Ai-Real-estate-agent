"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from typing import Annotated, Any

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.middleware import RequestIDMiddleware
from app.api.v1.router import api_v1_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.redis import close_redis, get_redis
from app.db.session import get_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """Startup / shutdown lifecycle hook."""
    setup_logging()
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")
    await close_redis()


app = FastAPI(
    title="AI Real Estate Sales Agent",
    description="Multi-tenant SaaS AI chatbot for real estate",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIDMiddleware)

# ── Routers ──────────────────────────────────────────────────────────
app.include_router(api_v1_router)

# ── Exception Handlers ───────────────────────────────────────────────
register_exception_handlers(app)


# ── Health Check ─────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check(
    db: Annotated[Session, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)],
) -> dict[str, Any]:
    """Check connectivity to PostgreSQL and Redis."""
    checks: dict[str, str] = {}

    # Database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"

    # Redis
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
