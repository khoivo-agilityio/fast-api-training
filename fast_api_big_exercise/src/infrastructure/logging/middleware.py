"""Logging middleware — logs every HTTP request/response.

Adds:
  - method, path, status_code, duration_ms to every request log
  - request_id (UUID) so you can trace a single request through all log lines
  - client IP address

Usage: registered automatically in create_app() via main.py.
"""

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every incoming request and its response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate a unique ID so all log lines for this request can be linked
        request_id = str(uuid.uuid4())[:8]

        # Bind request context to the logger for the duration of this request
        bound_logger = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )

        bound_logger.info("request_started")

        start = time.perf_counter()
        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            bound_logger.info(
                "request_finished",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            # Pass the request_id back to the client for debugging
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            bound_logger.exception(
                "request_failed",
                duration_ms=duration_ms,
                error=str(exc),
            )
            raise
