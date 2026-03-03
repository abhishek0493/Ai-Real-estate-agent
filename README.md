# AI Real Estate Sales Agent — Multi-Tenant SaaS

Production-grade B2B SaaS backend providing an embeddable AI chatbot for real estate companies.

## Stack

- **Backend:** Python FastAPI, PostgreSQL, Redis, Celery
- **Frontend:** Next.js (Dashboard + Widget)
- **AI:** LLM function calling with prompt versioning
- **Infra:** Docker, Terraform, AWS ECS (Fargate)

## Quick Start

```bash
cp .env.example .env
docker-compose up --build
```

## Project Structure

```
backend/         # FastAPI application (Clean Architecture)
frontend/        # Next.js dashboard & embeddable widget
infrastructure/  # Terraform IaC for AWS
scripts/         # Utility scripts
docs/            # Architecture & design documents
architecture/    # Architecture decision records
.github/         # CI/CD workflows
```

## License

Proprietary
