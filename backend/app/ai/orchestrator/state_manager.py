"""Conversation state manager — Redis-backed state tracking.

Provides a fast in-memory layer on top of PostgreSQL for per-lead
conversation context.  Every lead conversation gets a Redis hash
(state fields) and a capped list (message summaries).

Key schema
----------
{prefix}:conv:{lead_id}:state   → Hash  (lead status + collected fields + metadata)
{prefix}:conv:{lead_id}:history → List  (recent message role:snippet pairs, JSON)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis

from app.domain.entities.lead import Lead

logger = logging.getLogger(__name__)

# Maximum number of message summaries kept in the Redis list.
_MAX_HISTORY_LEN = 30

# Sentinel used when a field has no value yet (Redis hashes don't store None).
_EMPTY = ""


class ConversationStateManager:
    """Redis-backed conversation state for the AI orchestrator.

    This class does **not** replace PostgreSQL — it acts as a fast cache
    that keeps the current conversation context available in < 1 ms.
    """

    def __init__(
        self,
        redis: aioredis.Redis,
        *,
        key_prefix: str = "ai_re",
        ttl_seconds: int = 86400,
    ) -> None:
        self._redis = redis
        self._prefix = key_prefix
        self._ttl = ttl_seconds

    # ── Key builders ─────────────────────────────────────────────────

    def _state_key(self, lead_id: UUID) -> str:
        return f"{self._prefix}:conv:{lead_id}:state"

    def _history_key(self, lead_id: UUID) -> str:
        return f"{self._prefix}:conv:{lead_id}:history"

    # ── Public API ───────────────────────────────────────────────────

    async def initialize(self, lead: Lead) -> dict[str, str]:
        """Seed Redis with the current domain state of *lead*.

        Called on the first message of a conversation or on a cache miss.
        Overwrites any stale data that might exist.
        """
        now = datetime.now(timezone.utc).isoformat()
        state = self._lead_to_state(lead, created_at=now, updated_at=now)

        key = self._state_key(lead.id)
        pipe = self._redis.pipeline()
        pipe.delete(key)
        pipe.hset(key, mapping=state)
        pipe.expire(key, self._ttl)
        await pipe.execute()

        logger.debug("Initialized conversation state for lead %s", lead.id)
        return state

    async def get_state(self, lead_id: UUID) -> dict[str, str] | None:
        """Return the full conversation state hash, or ``None`` on miss."""
        data = await self._redis.hgetall(self._state_key(lead_id))
        return data if data else None

    async def sync_from_lead(self, lead: Lead) -> dict[str, str]:
        """Push the current domain entity state into Redis.

        Call this **after** the orchestrator has executed a tool and the
        Lead entity has been mutated in memory.
        """
        now = datetime.now(timezone.utc).isoformat()
        key = self._state_key(lead.id)

        # Preserve original created_at if it exists
        existing_created = await self._redis.hget(key, "created_at")
        created_at = existing_created or now

        state = self._lead_to_state(lead, created_at=created_at, updated_at=now)

        pipe = self._redis.pipeline()
        pipe.hset(key, mapping=state)
        pipe.expire(key, self._ttl)
        await pipe.execute()

        return state

    async def record_turn(
        self,
        lead_id: UUID,
        tool_name: str | None = None,
        error: str | None = None,
    ) -> None:
        """Increment turn count and record the last tool / error."""
        key = self._state_key(lead_id)

        pipe = self._redis.pipeline()
        pipe.hincrby(key, "turn_count", 1)
        pipe.hset(key, "last_tool", tool_name or _EMPTY)
        pipe.hset(key, "last_tool_error", error or _EMPTY)
        pipe.hset(key, "updated_at", datetime.now(timezone.utc).isoformat())
        pipe.expire(key, self._ttl)
        await pipe.execute()

    async def append_message_summary(
        self,
        lead_id: UUID,
        role: str,
        snippet: str,
    ) -> None:
        """Push a short message summary onto the history list.

        The list is capped at ``_MAX_HISTORY_LEN`` entries (FIFO).
        """
        key = self._history_key(lead_id)
        entry = json.dumps({
            "role": role,
            "snippet": snippet[:200],  # hard-cap to avoid bloat
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        pipe = self._redis.pipeline()
        pipe.rpush(key, entry)
        pipe.ltrim(key, -_MAX_HISTORY_LEN, -1)  # keep only the last N
        pipe.expire(key, self._ttl)
        await pipe.execute()

    async def get_message_summaries(
        self,
        lead_id: UUID,
        count: int = 10,
    ) -> list[dict[str, Any]]:
        """Return the most recent *count* message summaries."""
        key = self._history_key(lead_id)
        raw_entries = await self._redis.lrange(key, -count, -1)
        return [json.loads(entry) for entry in raw_entries]

    async def delete_state(self, lead_id: UUID) -> None:
        """Remove all Redis keys for a lead conversation."""
        pipe = self._redis.pipeline()
        pipe.delete(self._state_key(lead_id))
        pipe.delete(self._history_key(lead_id))
        await pipe.execute()
        logger.debug("Deleted conversation state for lead %s", lead_id)

    async def is_active(self, lead_id: UUID) -> bool:
        """Return ``True`` if a conversation state exists in Redis."""
        return await self._redis.exists(self._state_key(lead_id)) > 0

    # ── Internals ────────────────────────────────────────────────────

    @staticmethod
    def _lead_to_state(
        lead: Lead,
        *,
        created_at: str,
        updated_at: str,
    ) -> dict[str, str]:
        """Flatten a Lead entity into a Redis-compatible string dict."""
        return {
            "lead_id": str(lead.id),
            "lead_status": lead.status.value,
            "lead_name": lead.name,
            "preferred_location": lead.preferred_location or _EMPTY,
            "budget_min": str(lead.budget_min) if lead.budget_min is not None else _EMPTY,
            "budget_max": str(lead.budget_max) if lead.budget_max is not None else _EMPTY,
            "bedrooms": str(lead.bedrooms) if lead.bedrooms is not None else _EMPTY,
            "preferences": json.dumps(lead.preferences) if lead.preferences else "[]",
            "turn_count": "0",
            "last_tool": _EMPTY,
            "last_tool_error": _EMPTY,
            "created_at": created_at,
            "updated_at": updated_at,
        }
