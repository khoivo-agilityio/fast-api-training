"""
ASGI middleware stack:

1. ``request_context_middleware`` — injects a UUID request-id into
   structlog's contextvars so every log line carries it automatically.
2. ``timing_middleware``          — logs a rich ANSI-coloured request/response
   line to stdout (skips ``/health`` to avoid noise) and sets
   ``X-Process-Time`` + ``X-Request-ID`` response headers.
3. CORS is wired in ``create_app()`` via FastAPI's built-in middleware helper.

Register both with ``@app.middleware("http")`` in ``create_app()``.

Coloured log line format (dev/DEBUG):
    12:34:56.789 │ POST  /api/v1/auth/login  →  200 OK   [▓▓▓░░]  4.21 ms
"""

import sys
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime

import structlog
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)

# ── ANSI helpers ──────────────────────────────────────────────────────────────
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

# Foreground colours
_FG_WHITE = "\033[97m"
_FG_CYAN = "\033[96m"
_FG_GREEN = "\033[92m"
_FG_YELLOW = "\033[93m"
_FG_RED = "\033[91m"
_FG_GREY = "\033[90m"

# Background colours for method tags
_BG_GET = "\033[44m"  # blue bg
_BG_POST = "\033[42m"  # green bg
_BG_PUT = "\033[43m"  # yellow bg
_BG_PATCH = "\033[45m"  # magenta bg
_BG_DELETE = "\033[41m"  # red bg
_BG_OTHER = "\033[40m"  # black bg

# Paths to skip (too noisy in logs)
_SKIP_PATHS: frozenset[str] = frozenset({"/health", "/favicon.ico"})

# Duration bar config
_BAR_TOTAL = 5  # total segments in progress bar
_BAR_FAST_MS = 50  # ≤ this → all green
_BAR_SLOW_MS = 500  # ≥ this → all red


def _is_tty() -> bool:
    """Return True when stdout is a real terminal (enables ANSI colours)."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _method_tag(method: str, use_colour: bool) -> str:
    """Return a padded, coloured HTTP method tag, e.g. `` POST ``."""
    padded = f" {method:<6}"
    if not use_colour:
        return padded
    bg = {
        "GET": _BG_GET,
        "POST": _BG_POST,
        "PUT": _BG_PUT,
        "PATCH": _BG_PATCH,
        "DELETE": _BG_DELETE,
    }.get(method, _BG_OTHER)
    return f"{_BOLD}{bg}{_FG_WHITE}{padded}{_RESET}"


def _status_tag(status: int, use_colour: bool) -> str:
    """Return a coloured HTTP status string, e.g. ``200 OK``."""
    labels = {
        200: "OK",
        201: "Created",
        204: "No Content",
        301: "Moved",
        302: "Found",
        304: "Not Modified",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable",
        429: "Too Many Requests",
        500: "Server Error",
        502: "Bad Gateway",
        503: "Unavailable",
    }
    label = labels.get(status, "")
    text = f"{status} {label}".strip()
    if not use_colour:
        return text
    if status < 300:
        colour = _FG_GREEN
    elif status < 400:
        colour = _FG_CYAN
    elif status < 500:
        colour = _FG_YELLOW
    else:
        colour = _FG_RED
    return f"{_BOLD}{colour}{text}{_RESET}"


def _duration_bar(elapsed_ms: float, use_colour: bool) -> str:
    """Return a compact unicode progress bar reflecting response speed."""
    ratio = min(elapsed_ms / _BAR_SLOW_MS, 1.0)
    filled = round(ratio * _BAR_TOTAL)
    bar_chars = "▓" * filled + "░" * (_BAR_TOTAL - filled)
    if not use_colour:
        return f"[{bar_chars}]"
    if elapsed_ms <= _BAR_FAST_MS:
        colour = _FG_GREEN
    elif elapsed_ms <= _BAR_SLOW_MS:
        colour = _FG_YELLOW
    else:
        colour = _FG_RED
    return f"{colour}[{bar_chars}]{_RESET}"


def _duration_str(elapsed_ms: float, use_colour: bool) -> str:
    """Return a human-friendly duration, e.g. ``4.21 ms`` or ``1.23 s``."""
    if elapsed_ms >= 1_000:
        text = f"{elapsed_ms / 1_000:.3f} s"
    else:
        text = f"{elapsed_ms:.2f} ms"
    if not use_colour:
        return text
    if elapsed_ms <= _BAR_FAST_MS:
        colour = _FG_GREEN
    elif elapsed_ms <= _BAR_SLOW_MS:
        colour = _FG_YELLOW
    else:
        colour = _FG_RED
    return f"{_BOLD}{colour}{text}{_RESET}"


def _build_log_line(
    *,
    wall_time: datetime,
    method: str,
    path: str,
    status: int,
    elapsed_ms: float,
    request_id: str,
    use_colour: bool,
) -> str:
    """Assemble the full single-line log entry."""
    ts = wall_time.strftime("%H:%M:%S.") + f"{wall_time.microsecond // 1000:03d}"

    sep = f"{_DIM}│{_RESET}" if use_colour else "│"
    arrow = f"{_DIM}→{_RESET}" if use_colour else "→"
    rid_part = (
        f"  {_DIM}{_FG_GREY}{request_id[:8]}{_RESET}"
        if use_colour
        else f"  {request_id[:8]}"
    )
    ts_part = f"{_DIM}{ts}{_RESET}" if use_colour else ts
    path_part = f"{_FG_CYAN}{path}{_RESET}" if use_colour else path

    return (
        f"{ts_part}  {sep}  "
        f"{_method_tag(method, use_colour)}  "
        f"{path_part}  "
        f"{arrow}  "
        f"{_status_tag(status, use_colour):}  "
        f"{_duration_bar(elapsed_ms, use_colour)}  "
        f"{_duration_str(elapsed_ms, use_colour)}"
        f"{rid_part}"
    )


# ── Middleware functions ───────────────────────────────────────────────────────


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
    """
    Measure wall-clock time, emit a rich log line, and set response headers.

    * ``X-Process-Time`` — duration in milliseconds (e.g. ``4.21ms``)
    * ``X-Request-ID``   — already set by request_context_middleware upstream,
                           read back here so timing can include it in the log.

    ``/health`` (and other ``_SKIP_PATHS``) are processed normally but their
    log lines are suppressed to avoid cluttering the output.
    """
    start = time.perf_counter()
    wall_start = datetime.now()  # local wall time for display

    response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start) * 1_000
    response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"

    path = request.url.path

    # Always emit a structured JSON/contextvars log entry (picked up by
    # structlog's processor chain → goes to file / centralised logging)
    structlog.contextvars.bind_contextvars(
        status_code=response.status_code,
        duration_ms=round(elapsed_ms, 2),
    )
    await logger.ainfo("request_handled")

    # Suppress noisy health-check lines from the human-readable console output
    if path not in _SKIP_PATHS:
        request_id = response.headers.get("X-Request-ID", "")
        use_colour = _is_tty()
        line = _build_log_line(
            wall_time=wall_start,
            method=request.method,
            path=path,
            status=response.status_code,
            elapsed_ms=elapsed_ms,
            request_id=request_id,
            use_colour=use_colour,
        )
        print(line, flush=True)  # intentional console output — not a debug print

    return response
