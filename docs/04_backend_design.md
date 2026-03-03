# Backend Principles

- Clean Architecture
- Repository Pattern
- Service Layer
- Dependency Injection
- Pydantic schemas
- DTO separation

# Folder Structure

backend/
app/
api/
core/
models/
schemas/
services/
repositories/
ai/
tasks/
tests/

# API Routes

POST /chat
POST /tenant/register
POST /auth/login
GET /admin/leads
GET /admin/properties
POST /admin/properties

# Backend Philosophy

Follow Clean Architecture.

Layers:

1. Presentation Layer (FastAPI routes)
2. Application Layer (Use Cases)
3. Domain Layer (Business Logic)
4. Infrastructure Layer (DB, Redis, Email, LLM)

# Enforce:

- No business logic in controllers
- No direct DB access in routes
- All DB access via repositories
- All AI calls via orchestrator service

# Dependency Injection

Use FastAPI Depends for service wiring.
