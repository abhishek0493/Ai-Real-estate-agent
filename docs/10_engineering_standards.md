# Code Quality Standards

- Type hints everywhere
- Strict mypy validation
- Black + Ruff formatting
- Pre-commit hooks
- Conventional commits
- GitHub PR workflow

# Architecture Rules

- No business logic inside route handlers
- No DB queries inside services without repository layer
- No LLM calls inside controllers
- Dependency injection required

# Error Handling

- Centralized exception handler
- Structured error responses
- No raw exception leaks

# Logging

- Correlation ID per request
- JSON structured logs
