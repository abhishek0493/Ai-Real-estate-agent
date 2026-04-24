# AI Real Estate Agent — Developer Guide

> Complete guide to understanding, running, and testing the AI Real Estate Sales Agent

---

## Table of Contents

1. [What is This App?](#what-is-this-app)
2. [Architecture Overview](#architecture-overview)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [How the App Works — End to End](#how-the-app-works--end-to-end)
6. [Lead State Machine](#lead-state-machine)
7. [AI Orchestrator Pipeline](#ai-orchestrator-pipeline)
8. [Redis State Management](#redis-state-management)
9. [API Endpoints Reference](#api-endpoints-reference)
10. [Running the App Locally](#running-the-app-locally)
11. [Testing with cURL](#testing-with-curl)
12. [Running Tests](#running-tests)
13. [Troubleshooting](#troubleshooting)

---

## What is This App?

This is a **multi-tenant SaaS AI chatbot** for real estate companies. A buyer chats with the AI agent, which conversationally collects their requirements (location, budget, bedrooms), searches a property database for matches, and connects them with a human agent.

**Key features:**

- 🤖 **AI-powered conversations** — Uses OpenAI GPT to have natural property-buying conversations
- 🏢 **Multi-tenant** — Multiple real estate companies can use the same platform, each isolated by API key
- 🔒 **JWT Authentication** — Dashboard users (agents, admins) authenticate with JWT tokens
- 📊 **State machine** — Leads progress through a defined lifecycle (INIT → COLLECTING → MATCHING → etc.)
- ⚡ **Redis caching** — Conversation state is cached in Redis for sub-millisecond access
- 🐘 **PostgreSQL** — Persistent storage for leads, properties, conversations, tenants, users

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Client (cURL / Frontend)                     │
│                   Sends: X-Tenant-Key header + message              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (:8000)                          │
│                                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────────────────┐  │
│  │ API      │──▶│ ChatService  │──▶│ AIOrchestrator             │  │
│  │ Router   │   │              │   │  ├── PromptBuilder         │  │
│  │ (chat.py)│   │  • Resolve   │   │  ├── LLMClient (OpenAI)   │  │
│  │          │   │    lead      │   │  ├── ToolRegistry          │  │
│  │          │   │  • Load      │   │  ├── ToolValidator         │  │
│  │          │   │    history   │   │  └── StateManager (Redis)  │  │
│  │          │   │  • Persist   │   │                            │  │
│  │          │   │    messages  │   │  LLM ↔ Tool loop:          │  │
│  │          │   │              │   │  1. Build prompt            │  │
│  └──────────┘   └──────────────┘   │  2. Call GPT               │  │
│                                     │  3. Validate tool call     │  │
│                                     │  4. Execute tool           │  │
│                                     │  5. Follow-up LLM call    │  │
│                                     │  6. Return response        │  │
│                                     └────────────────────────────┘  │
│                                                                     │
│  ┌─────────────┐          ┌──────────────┐                          │
│  │ PostgreSQL  │          │    Redis      │                          │
│  │ ─────────── │          │ ──────────── │                          │
│  │ • tenants   │          │ • conv state │                          │
│  │ • leads     │          │   (hash)     │                          │
│  │ • messages  │          │ • msg history│                          │
│  │ • properties│          │   (list)     │                          │
│  │ • users     │          │ • 24h TTL    │                          │
│  └─────────────┘          └──────────────┘                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer             | Technology                                   |
| ----------------- | -------------------------------------------- |
| **API Framework** | FastAPI + Uvicorn                            |
| **Database**      | PostgreSQL 15 (via SQLAlchemy 2.0 + asyncpg) |
| **Migrations**    | Alembic                                      |
| **Cache**         | Redis 7                                      |
| **Task Queue**    | Celery (Redis broker)                        |
| **LLM**           | OpenAI GPT (gpt-3.5-turbo / gpt-4o-mini)     |
| **Auth**          | JWT (python-jose) + bcrypt                   |
| **Container**     | Docker + docker compose                      |
| **Language**      | Python 3.11+                                 |

---

## Project Structure

```
AI Real estate agent/
├── .env                          # Environment variables
├── .env.example                  # Template for .env
├── docker compose.yml            # Spins up backend + postgres + redis + celery
├── Makefile                      # Convenience commands (make up, make test, etc.)
│
├── backend/
│   ├── Dockerfile                # Python 3.11-slim container
│   ├── requirements.txt          # Python dependencies
│   ├── alembic.ini               # Alembic config for migrations
│   ├── alembic/                  # Migration scripts
│   ├── entrypoint.sh             # Runs migrations → starts uvicorn
│   │
│   ├── app/
│   │   ├── main.py               # FastAPI app entry point + lifespan
│   │   │
│   │   ├── api/v1/               # API route handlers
│   │   │   ├── chat.py           # POST /api/v1/chat — main AI endpoint
│   │   │   ├── auth.py           # POST /register, /login, GET /me
│   │   │   ├── admin.py          # GET /admin/dashboard (JWT protected)
│   │   │   ├── admin_leads.py    # CRUD leads (JWT protected)
│   │   │   ├── admin_properties.py  # CRUD properties (SUPER_ADMIN)
│   │   │   └── admin_users.py    # User management (SUPER_ADMIN)
│   │   │
│   │   ├── ai/                   # AI / LLM layer
│   │   │   ├── llm/base.py       # Abstract LLMClient interface
│   │   │   ├── llm/openai_client.py  # OpenAI implementation
│   │   │   ├── orchestrator/
│   │   │   │   ├── engine.py     # AIOrchestrator — main AI pipeline
│   │   │   │   ├── prompt_builder.py  # Assembles system prompts
│   │   │   │   └── state_manager.py   # Redis-backed conversation state
│   │   │   ├── prompts/v1/       # Versioned prompt templates
│   │   │   │   └── system_prompt.txt  # The AI persona + rules
│   │   │   └── tools/            # LLM function-calling tools
│   │   │       ├── registry.py   # Tool name → handler mapping
│   │   │       ├── validator.py  # State-aware tool validation
│   │   │       ├── lead_tools.py # Tools: set_location, update_budget, etc.
│   │   │       └── property_tools.py  # Tools: get_matching_properties, etc.
│   │   │
│   │   ├── domain/               # Pure domain layer (no framework deps)
│   │   │   ├── entities/lead.py  # Lead entity + LeadStatus enum
│   │   │   ├── state_machine/    # Lead state transition rules
│   │   │   ├── negotiation/      # Budget negotiation engine
│   │   │   ├── services/         # LeadFlowService
│   │   │   └── exceptions.py     # DomainException hierarchy
│   │   │
│   │   ├── core/                 # App infrastructure
│   │   │   ├── config.py         # Pydantic Settings (env vars)
│   │   │   ├── redis.py          # Redis client + lifecycle
│   │   │   ├── security.py       # JWT + password hashing
│   │   │   └── logging.py        # Structured JSON logging
│   │   │
│   │   ├── models/               # SQLAlchemy models
│   │   ├── repositories/         # Data access layer
│   │   ├── services/             # Application services
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   └── dependencies/         # FastAPI dependencies (auth, tenant)
│   │
│   └── tests/
│       ├── conftest.py           # DB fixtures (lazy-loaded)
│       └── unit/
│           └── test_state_manager.py  # Redis state manager tests
│
├── frontend/                     # Next.js (dashboard + chat widget)
├── docs/                         # Design documents
└── architecture/                 # Architecture notes
```

---

## How the App Works — End to End

Here's what happens when a buyer sends a chat message:

### 1. API Request Arrives

```http
POST /api/v1/chat
X-Tenant-Key: <tenant-api-key>
Content-Type: application/json

{
  "message": "I want to buy a 2BHK flat in Mumbai",
  "lead_id": null
}
```

### 2. Tenant Resolution

The `X-Tenant-Key` header is resolved to a `TenantModel` via `get_current_tenant`. This ensures all data is scoped to the correct real estate company. If the key is invalid → `401`.

### 3. ChatService Orchestrates Everything

```
ChatService.handle_message()
│
├── 1. Resolve or create lead (LeadModel in PostgreSQL)
│      • If lead_id is null → create new lead in INIT state
│      • If lead_id provided → look up existing lead
│
├── 2. Load conversation history from PostgreSQL (last 20 messages)
│
├── 3. Convert DB model → domain entity (Lead)
│
├── 3a. Initialize Redis state (if cache miss)
│       • ConversationStateManager.get_state() → None?
│       • → ConversationStateManager.initialize(lead)
│
├── 4. Call AIOrchestrator.process_message()  ← The AI magic happens here
│
├── 5. Apply domain changes back to DB model
│
├── 6. Persist user + assistant messages to PostgreSQL
│
├── 7. Commit transaction
│
└── 8. Append message summaries to Redis (non-critical)
```

### 4. AI Orchestrator Pipeline

```
AIOrchestrator.process_message()
│
├── Build system prompt (persona + context + rules)
│    └── Injects: collected fields, missing fields, allowed tools
│
├── Call OpenAI GPT with messages + tool schemas
│
├── If LLM returns a tool call:
│    ├── Validate: tool exists? params present? allowed in current state?
│    │    └── On failure → recovery LLM call (hide error, ask follow-up)
│    │
│    ├── Execute tool handler (e.g., set_location, get_matching_properties)
│    │    └── On failure → recovery LLM call
│    │
│    ├── Follow-up LLM call: tell GPT the result, ask it to respond naturally
│    │
│    ├── Sync lead state to Redis
│    └── Record turn in Redis
│
└── If plain text → record turn, return message
```

### 5. Response Returned

```json
{
  "assistant_message": "Great! I found 3 properties matching your requirements...",
  "lead_id": "a1b2c3d4-...",
  "current_status": "MATCHING_PROPERTIES",
  "tool_executed": "get_matching_properties",
  "error": null
}
```

---

## Lead State Machine

Every lead progresses through a strict state machine. Invalid transitions are rejected.

```mermaid
graph TD
    A["INIT"] -->|"start_collection"| B["COLLECTING_REQUIREMENTS"]
    B -->|"validate_budget"| C["VALIDATING_BUDGET"]
    C -->|"move_to_matching"| D["MATCHING_PROPERTIES"]
    D -->|"start_negotiation"| E["NEGOTIATING"]
    E -->|"confirm_interest"| F["CONFIRMING"]
    F -->|"interested=true"| G["INTERESTED"]
    F -->|"interested=false"| H["NOT_INTERESTED"]
    G --> I["CLOSED"]
    H --> I
```

**Tools allowed per state:**

| State                     | Allowed Tools                                                                            |
| ------------------------- | ---------------------------------------------------------------------------------------- |
| `INIT`                    | `start_collection`                                                                       |
| `COLLECTING_REQUIREMENTS` | `update_budget`, `set_location`, `set_bedrooms`, `update_preferences`, `validate_budget` |
| `VALIDATING_BUDGET`       | `move_to_matching`                                                                       |
| `MATCHING_PROPERTIES`     | `get_matching_properties`, `start_negotiation`                                           |
| `NEGOTIATING`             | `evaluate_budget`, `confirm_interest`                                                    |
| `CONFIRMING`              | `confirm_interest`                                                                       |

---

## AI Orchestrator Pipeline

The orchestrator sits between the LLM and the domain layer, ensuring safe execution:

```
User Message
     │
     ▼
┌─────────────────┐
│  PromptBuilder   │  Assembles: system prompt + context + history + user message
└────────┬────────┘
         ▼
┌─────────────────┐
│   LLM (GPT)     │  Returns: plain text OR tool call
└────────┬────────┘
         │
         ├─── Plain text? → Return directly
         │
         └─── Tool call?
              │
              ▼
         ┌─────────────────┐
         │  ToolValidator   │  Check: exists? params? allowed in state?
         └────────┬────────┘
                  │
                  ├─── Invalid? → Recovery LLM call (ask follow-up, hide error)
                  │
                  └─── Valid?
                       │
                       ▼
                  ┌─────────────────┐
                  │  Tool Handler    │  Execute: set_location(), get_matching_properties(), etc.
                  └────────┬────────┘
                           │
                           ├─── Domain error? → Recovery LLM call
                           │
                           └─── Success?
                                │
                                ▼
                           ┌─────────────────┐
                           │  Follow-up LLM   │  "Based on result, respond naturally"
                           └────────┬────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │  Sync Redis      │  sync_from_lead() + record_turn()
                           └────────┬────────┘
                                    │
                                    ▼
                              AIResponse
```

---

## Redis State Management

Redis provides a fast cache layer alongside PostgreSQL. Every lead conversation has two Redis keys:

```
ai_re:conv:{lead_id}:state    → Hash (lead status, fields, turn count, last tool)
ai_re:conv:{lead_id}:history  → List (capped at 30 message summaries)
```

- **TTL**: 24 hours (auto-expires stale conversations)
- **Non-critical**: If Redis is down, the app falls back to PostgreSQL only
- **Pipeline batching**: All Redis ops use `pipeline()` for single round-trips

---

## API Endpoints Reference

### Chat (Public — requires `X-Tenant-Key`)

| Method | Endpoint       | Description                    |
| ------ | -------------- | ------------------------------ |
| `POST` | `/api/v1/chat` | Send a message to the AI agent |

### Auth (requires `X-Tenant-Key`)

| Method | Endpoint                | Description                     |
| ------ | ----------------------- | ------------------------------- |
| `POST` | `/api/v1/auth/register` | Register a dashboard user       |
| `POST` | `/api/v1/auth/login`    | Login → JWT token               |
| `GET`  | `/api/v1/auth/me`       | Get current user (JWT required) |

### Admin (requires JWT)

| Method   | Endpoint                        | Description                        |
| -------- | ------------------------------- | ---------------------------------- |
| `GET`    | `/api/v1/admin/dashboard`       | Dashboard summary                  |
| `GET`    | `/api/v1/admin/leads`           | List all leads                     |
| `GET`    | `/api/v1/admin/leads/{id}`      | Lead detail + conversation history |
| `GET`    | `/api/v1/admin/properties`      | List all properties                |
| `POST`   | `/api/v1/admin/properties`      | Add a property (SUPER_ADMIN)       |
| `DELETE` | `/api/v1/admin/properties/{id}` | Remove a property (SUPER_ADMIN)    |

### System

| Method | Endpoint  | Description                           |
| ------ | --------- | ------------------------------------- |
| `GET`  | `/health` | Check PostgreSQL + Redis connectivity |

---

## Running the App Locally

### Prerequisites

- **Docker Desktop** installed and running
- **OpenAI API Key** ([get one here](https://platform.openai.com/api-keys))

### Step 1: Clone and Configure

```bash
git clone https://github.com/abhishek0493/Ai-Real-estate-agent.git
cd Ai-Real-estate-agent

# Create .env from template
cp .env.example .env
```

Edit `.env` and set your **OpenAI API key**:

```env
LLM_API_KEY=sk-proj-your-actual-key-here
LLM_MODEL=gpt-3.5-turbo
```

> [!TIP]
> Use `gpt-3.5-turbo` for fast/cheap testing. Switch to `gpt-4o-mini` or `gpt-4o` for better quality.

### Step 2: Start All Services

```bash
# Build and start everything (backend, postgres, redis, celery worker)
make build
make up

# Or directly:
docker compose up -d --build
```

This starts:

- **Backend** → `http://localhost:8000`
- **PostgreSQL** → `localhost:5433`
- **Redis** → `localhost:6379`
- **Celery Worker** → background processing

### Step 3: Run Database Migrations

```bash
make migrate

# Or directly:
docker compose exec backend alembic upgrade head
```

### Step 4: Provision a Test Tenant

You need a tenant to make API calls. Use the admin provisioning endpoint or create one directly:

```bash
# Connect to the running backend container
docker compose exec backend python -c "
from app.core.config import get_settings
from app.db.session import _get_session_factory
from app.services.tenant_provisioning_service import TenantProvisioningService

settings = get_settings()
SessionLocal = _get_session_factory(settings)
db = SessionLocal()
service = TenantProvisioningService(db)
tenant = service.provision_full(name='Demo Realty', email='demo@realty.com')
print(f'Tenant ID:  {tenant.id}')
print(f'API Key:    {tenant.api_key}')
print('Properties seeded: 10 Mumbai locations')
db.close()
"
```

> [!IMPORTANT]
> **Save the `API Key`** — you'll need it as the `X-Tenant-Key` header for all API calls.

### Step 5: Verify Everything is Running

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "checks": {
    "database": "ok",
    "redis": "ok"
  }
}
```

### Step 6: Open the API Docs

Visit **http://localhost:8000/docs** to see the interactive Swagger UI.

---

## Testing with cURL

### Complete Chat Flow — From Hello to Property Match

Below is a full end-to-end conversation. Replace `YOUR_TENANT_API_KEY` with the key from Step 4.

#### Turn 1: Start the conversation

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: YOUR_TENANT_API_KEY" \
  -d '{"message": "Hi, I want to buy a flat"}' | python3 -m json.tool
```

The AI will greet you and start collecting requirements. **Save the `lead_id` from the response** — you'll use it for subsequent turns.

#### Turn 2: Provide location

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: YOUR_TENANT_API_KEY" \
  -d '{
    "message": "I am looking for something in Andheri",
    "lead_id": "LEAD_ID_FROM_TURN_1"
  }' | python3 -m json.tool
```

#### Turn 3: Provide bedrooms

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: YOUR_TENANT_API_KEY" \
  -d '{
    "message": "2 BHK please",
    "lead_id": "LEAD_ID_FROM_TURN_1"
  }' | python3 -m json.tool
```

#### Turn 4: Provide budget

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: YOUR_TENANT_API_KEY" \
  -d '{
    "message": "My budget is around 70 to 90 lakhs",
    "lead_id": "LEAD_ID_FROM_TURN_1"
  }' | python3 -m json.tool
```

At this point, the AI should:

1. Call `validate_budget` → `move_to_matching` → `get_matching_properties`
2. Search the database for 2BHK properties in Andheri within ₹70-90 lakhs
3. Present matching properties in a formatted list

#### Turn 5: Provide everything at once (alternative)

You can also give all info in one message:

```bash
curl -s -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: YOUR_TENANT_API_KEY" \
  -d '{
    "message": "I want a 2BHK in Andheri, budget 70-90 lakhs"
  }' | python3 -m json.tool
```

### Auth Flow — Register and Login

```bash
# Register a dashboard user
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: YOUR_TENANT_API_KEY" \
  -d '{
    "email": "agent@demo.com",
    "password": "securepass123",
    "role": "AGENT"
  }' | python3 -m json.tool

# Login to get a JWT token
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Key: YOUR_TENANT_API_KEY" \
  -d '{
    "email": "agent@demo.com",
    "password": "securepass123"
  }' | python3 -m json.tool

# Use the token to access the admin dashboard
curl -s http://localhost:8000/api/v1/admin/dashboard \
  -H "X-Tenant-Key: YOUR_TENANT_API_KEY" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" | python3 -m json.tool

# View all leads
curl -s http://localhost:8000/api/v1/admin/leads \
  -H "X-Tenant-Key: YOUR_TENANT_API_KEY" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" | python3 -m json.tool
```

### Inspect Redis State

While the app is running, you can peek at Redis:

```bash
# Connect to Redis CLI inside Docker
docker compose exec redis redis-cli

# List all conversation state keys
KEYS ai_re:conv:*

# View state for a specific lead
HGETALL ai_re:conv:<lead_id>:state

# View message summaries
LRANGE ai_re:conv:<lead_id>:history 0 -1

# Check TTL
TTL ai_re:conv:<lead_id>:state
```

---

## Running Tests

### Unit Tests (Redis-only, no DB required)

```bash
# From host machine (venv must be active)
source .venv/bin/activate
cd backend
python -m pytest tests/unit/ -v

# Or inside Docker
docker compose exec backend pytest tests/unit/ -v
```

### Integration Tests (requires PostgreSQL)

```bash
# Inside Docker (DB is available)
docker compose exec backend pytest tests/ -v

# Or via Makefile
make test
```

### Run a Specific Test

```bash
python -m pytest tests/unit/test_state_manager.py::test_initialize_seeds_state -v
```

### Test Coverage

```bash
python -m pytest tests/ --cov=app --cov-report=html
# Open htmlcov/index.html in your browser
```

---

## Troubleshooting

### "Could not translate host name 'postgres'"

This means you're running outside Docker. The `DATABASE_URL` in `.env` uses `postgres` as the hostname (Docker service name). For local development without Docker:

```env
DATABASE_URL=postgresql://postgres:changeme@localhost:5433/ai_real_estate
REDIS_URL=redis://localhost:6379/0
```

### "Invalid or inactive API key" (401)

You haven't provisioned a tenant yet, or the `X-Tenant-Key` header is wrong. See [Step 4](#step-4-provision-a-test-tenant).

### "email-validator is not installed"

```bash
pip install email-validator
```

### Redis shows "unavailable" in /health

Make sure Redis is running:

```bash
docker compose ps redis
# Should show "Up"
```

### LLM returns empty or errors

- Check that `LLM_API_KEY` in `.env` is a valid OpenAI key
- Check OpenAI billing — free tier has low rate limits
- Try switching `LLM_MODEL` to `gpt-3.5-turbo` for testing

### Tests fail with "OperationalError: could not connect to server"

The integration tests need PostgreSQL. Either:

- Run them inside Docker: `make test`
- Or start Postgres locally on port 5433

### Viewing Logs

```bash
# All services
docker compose logs -f

# Just the backend
docker compose logs -f backend

# Celery worker
docker compose logs -f celery-worker
```

---

## Quick Reference — Makefile Commands

| Command        | Description          |
| -------------- | -------------------- |
| `make up`      | Start all services   |
| `make down`    | Stop all services    |
| `make build`   | Build all containers |
| `make test`    | Run backend tests    |
| `make lint`    | Run ruff linting     |
| `make migrate` | Run DB migrations    |
| `make seed`    | Seed the database    |
