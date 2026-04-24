.PHONY: help up down build test lint migrate seed

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build all containers
	docker compose build

test: ## Run backend tests
	docker compose exec backend pytest

lint: ## Run linting
	docker compose exec backend ruff check .

migrate: ## Run database migrations
	docker compose exec backend alembic upgrade head

seed: ## Seed the database
	docker compose exec backend python scripts/seed_db.py
