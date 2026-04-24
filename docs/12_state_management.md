# AI State Manager — Redis-Backed Conversation State Tracking

The `state_manager.py` file is currently empty (just a docstring). The goal is to build a production-grade `ConversationStateManager` that uses Redis to track per-lead conversation state in real-time, providing a fast in-memory layer that complements the existing PostgreSQL persistence.

## Why Redis?

Currently, every chat request:
1. Loads the `LeadModel` from PostgreSQL
2. Loads conversation history from PostgreSQL (last 20 messages)
3. Converts to a domain entity, runs the AI pipeline, writes back

This is fine for correctness but adds latency on every turn. Redis gives us:
- **Fast state lookups** — lead status, collected fields, turn count available in <1ms
- **Session-scoped context** — track per-conversation metadata (turn count, last tool used, timestamps) without extra DB queries
- **TTL-based cleanup** — stale conversations auto-expire (24h default)
- **Cross-service visibility** — Celery workers and other services can read conversation state without touching PostgreSQL

## Proposed Changes

### Component 1: Core Redis Module

#### [MODIFY] [redis.py](file:///Users/abhishek0493/AI%20Real%20estate%20agent/backend/app/core/redis.py)

Add a non-FastAPI utility function `get_redis_client()` that can be called from service-layer code without needing `Depends()`. The existing `get_redis()` dependency stays untouched.

---

### Component 2: Config Updates

#### [MODIFY] [config.py](file:///Users/abhishek0493/AI%20Real%20estate%20agent/backend/app/core/config.py)

Add two new settings:
- `REDIS_STATE_TTL_SECONDS: int = 86400` — default 24-hour TTL for conversation state keys
- `REDIS_KEY_PREFIX: str = "ai_re"` — namespace prefix to avoid key collisions

---

### Component 3: State Manager (main implementation)

#### [MODIFY] [state_manager.py](file:///Users/abhishek0493/AI%20Real%20estate%20agent/backend/app/ai/orchestrator/state_manager.py)

Full implementation of `ConversationStateManager`:

**Redis key schema:**
```
{prefix}:conv:{lead_id}:state    → Hash with all state fields
{prefix}:conv:{lead_id}:history  → List of recent message summaries (capped at 30)
```

**State hash fields:**
| Field | Type | Description |
|---|---|---|
| `lead_status` | str | Current `LeadStatus` value |
| `lead_name` | str | Lead name |
| `preferred_location` | str | Collected location |
| `budget_min` | str | Collected budget min (stored as string) |
| `budget_max` | str | Collected budget max (stored as string) |
| `bedrooms` | str | Collected bedrooms |
| `preferences` | str | JSON-encoded list of preferences |
| `turn_count` | str | Number of conversation turns |
| `last_tool` | str | Last tool that was executed |
| `last_tool_error` | str | Last tool error (if any) |
| `created_at` | str | ISO timestamp of session creation |
| `updated_at` | str | ISO timestamp of last update |

**Class API:**

```python
class ConversationStateManager:
    async def initialize(lead: Lead) -> dict
        # Seed Redis with current lead state (called on first message or cache miss)

    async def get_state(lead_id: UUID) -> dict | None
        # Fast read of the conversation state hash

    async def sync_from_lead(lead: Lead) -> dict
        # Push domain entity changes into Redis after tool execution

    async def record_turn(lead_id: UUID, tool_name: str | None, error: str | None) -> None
        # Increment turn count, record last tool/error

    async def append_message_summary(lead_id: UUID, role: str, snippet: str) -> None
        # Push a short message summary to the history list (capped)

    async def get_message_summaries(lead_id: UUID, count: int = 10) -> list[dict]
        # Fetch recent message summaries from Redis

    async def delete_state(lead_id: UUID) -> None
        # Explicitly remove state (e.g., on lead close)

    async def is_active(lead_id: UUID) -> bool
        # Check if a conversation state exists in Redis
```

---

### Component 4: Orchestrator Integration

#### [MODIFY] [engine.py](file:///Users/abhishek0493/AI%20Real%20estate%20agent/backend/app/ai/orchestrator/engine.py)

Update `AIOrchestrator.__init__` to accept an optional `ConversationStateManager`. After tool execution and response generation, call `sync_from_lead()` and `record_turn()` to keep Redis in sync.

---

### Component 5: ChatService Integration

#### [MODIFY] [chat_service.py](file:///Users/abhishek0493/AI%20Real%20estate%20agent/backend/app/services/chat_service.py)

Wire the `ConversationStateManager` into the service:
1. On `handle_message`, try `get_state()` first as a fast path for context
2. After AI response, call `sync_from_lead()` and `append_message_summary()`
3. Pass the state manager through to the orchestrator

---

### Component 6: Chat API Route

#### [MODIFY] [chat.py](file:///Users/abhishek0493/AI%20Real%20estate%20agent/backend/app/api/v1/chat.py)

Inject the Redis dependency and pass it through to `ChatService` → `ConversationStateManager`.

---

### Component 7: Application Lifecycle

#### [MODIFY] [main.py](file:///Users/abhishek0493/AI%20Real%20estate%20agent/backend/app/main.py)

Add Redis connection cleanup on shutdown in the lifespan handler.

---

### Component 8: Tests

#### [NEW] [test_state_manager.py](file:///Users/abhishek0493/AI%20Real%20estate%20agent/backend/tests/test_state_manager.py)

Unit tests using `fakeredis` for:
- `initialize` → seeds state correctly
- `get_state` / `sync_from_lead` → round-trip consistency
- `record_turn` → increments turn count, records tool info
- `append_message_summary` / `get_message_summaries` → capped list behavior
- `delete_state` / `is_active` → cleanup behavior
- TTL is set correctly on keys

## Open Questions

> [!IMPORTANT]
> **TTL duration**: I'm defaulting to 24 hours for conversation state expiry. Should stale conversations live longer (e.g., 7 days) or shorter?

> [!NOTE]
> **fakeredis dependency**: The tests will need `fakeredis[aioredis]` added to `requirements.txt`. This is a dev-only dependency used widely in the Python ecosystem.

## Verification Plan

### Automated Tests
- Run `pytest backend/tests/test_state_manager.py -v` to validate all state manager operations
- Run existing test suite to confirm no regressions

### Manual Verification
- Inspect Redis keys using `redis-cli` after a chat interaction to confirm correct schema
