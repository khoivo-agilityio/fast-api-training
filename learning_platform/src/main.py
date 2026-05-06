"""
App Factory — FastAPI application entry point.

Creates the FastAPI app, mounts routers, registers global exception
handlers, and configures lifespan events (startup/shutdown).
"""

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

# Status code mapping — walks MRO to find first matching parent (gotchas.md #2)
_STATUS_MAP: dict[type, int] = {
    NotFoundError: 404,
    AuthenticationError: 401,
    AuthorizationError: 403,
    ConflictError: 409,
    ValidationError: 422,
    DomainError: 400,
}


def _resolve_status(exc: DomainError) -> int:
    """Walk the MRO to find the first matching status code.

    This avoids the bug where subclass exceptions (e.g. InvalidCredentials)
    miss their parent's mapped status code (see gotchas.md #2).
    """
    for cls in type(exc).__mro__:
        if cls in _STATUS_MAP:
            return _STATUS_MAP[cls]
    return 400


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    yield
    # Shutdown — close Redis connection
    from src.redis import redis_client

    await redis_client.aclose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler for DomainError hierarchy
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=_resolve_status(exc),
            content={"detail": exc.detail, "error_code": exc.error_code},
        )

    # Mount routers
    from src.auth.router import router as auth_router
    from src.courses.router import router as courses_router
    from src.lessons.router import router as lessons_router
    from src.users.router import router as users_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(courses_router, prefix="/api/v1")
    app.include_router(lessons_router, prefix="/api/v1")

    # Health check
    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    return app


app = create_app()
