"""API middleware — request ID (correlation ID)."""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import correlation_id_ctx


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique X-Request-ID into every request/response cycle."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in context var so the JSON logger can pick it up
        token = correlation_id_ctx.set(request_id)

        # Make accessible via request.state for downstream handlers
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        finally:
            correlation_id_ctx.reset(token)

        response.headers["X-Request-ID"] = request_id
        return response
