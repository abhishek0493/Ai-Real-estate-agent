"""Structured JSON logging configuration."""

import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Context variable for per-request correlation ID
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")


class JSONFormatter(logging.Formatter):
    """Produces JSON-structured log lines."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get("-"),
            "logger": record.name,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with JSON output to stdout."""
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    # Quiet down noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
