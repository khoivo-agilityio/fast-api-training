"""FastAPI application factory, lifespan, global exception handlers, and health check."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)
from src.logging import configure_logging, logger
from src.redis import close_redis, get_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — connect/disconnect Redis."""
    configure_logging(debug=settings.DEBUG)
    logger.info("Starting application", app_name=settings.APP_NAME)
    # Eagerly connect Redis so health check works immediately
    await get_redis()
    yield
    await close_redis()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Exception Handlers ────────────────────────────────────────────────

_STATUS_MAP: dict[type[DomainError], int] = {
    NotFoundError: 404,
    AuthenticationError: 401,
    AuthorizationError: 403,
    ConflictError: 409,
    ValidationError: 422,
}


def _resolve_status(exc: DomainError) -> int:
    """Walk the MRO to find the status code for the exception or its parent."""
    for cls in type(exc).__mro__:
        if cls in _STATUS_MAP:
            return _STATUS_MAP[cls]
    return 400


@app.exception_handler(DomainError)
async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    status = _resolve_status(exc)
    return JSONResponse(
        status_code=status,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


# ── Routers ──────────────────────────────────────────────────────────────────
from src.auth.router import router as auth_router  # noqa: E402
from src.users.router import router as users_router  # noqa: E402

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


# ── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Health check — verifies DB and Redis connectivity."""
    from sqlalchemy import text

    from src.database import AsyncSessionFactory

    db_status = "ok"
    redis_status = "ok"

    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        client = await get_redis()
        await client.ping()
    except Exception:
        redis_status = "error"

    status = "healthy" if db_status == "ok" and redis_status == "ok" else "unhealthy"
    return {"status": status, "db": db_status, "redis": redis_status}
