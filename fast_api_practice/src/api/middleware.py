"""
ASGI middleware stack:

1. ``request_context_middleware`` — injects a UUID request-id into
   structlog's contextvars so every log line carries it automatically.
2. ``timing_middleware``          — adds an ``X-Process-Time`` response header.
3. CORS is wired in ``create_app()`` via FastAPI's built-in middleware helper.

Register both with ``@app.middleware("http")`` in ``create_app()``.
"""

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Bind a unique request-id to structlog context for each request."""
    request_id = str(uuid.uuid4())

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def timing_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Add ``X-Process-Time`` header (milliseconds) to every response."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1_000
    response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"

    await logger.ainfo(
        "request_handled",
        status_code=response.status_code,
        duration_ms=round(elapsed_ms, 2),
    )
    return response
