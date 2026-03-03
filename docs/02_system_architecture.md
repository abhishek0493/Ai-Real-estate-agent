# Architecture Style

Modular Monolith with Clean Architecture principles.

# Tech Stack

Backend:

- FastAPI (Python)
- PostgreSQL
- SQLAlchemy
- Redis (for caching conversation state)
- Celery (for async tasks like email)

Frontend:

- Next.js (React + TypeScript)
- Tailwind CSS
- ShadCN UI

AI Layer:

- LLM integration abstraction layer
- Prompt templates
- Function calling for DB lookup

DevOps:

- Docker
- Docker Compose
- NGINX
- GitHub Actions CI
- Deployed on Render / AWS / Railway

# High-Level Flow

User → Chat Widget → API → AI Orchestrator → DB Lookup → AI Response → Lead Storage → Email Service

# Deployment Target

AWS ECS (Fargate)
RDS PostgreSQL
ElastiCache Redis

# Service Separation

- backend-service (FastAPI)
- worker-service (Celery)
- postgres (RDS)
- redis (ElastiCache)

# Networking

- Private RDS subnet
- Public ALB
- HTTPS via ACM
