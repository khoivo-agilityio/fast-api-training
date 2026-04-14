from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.middleware import request_context_middleware, timing_middleware
from src.api.v1 import auth, comments, projects, tasks, users
from src.core.config import get_settings
from src.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainValidationError,
    NotFoundError,
)
from src.infrastructure.logging.setup import configure_logging
from src.schemas.common import ErrorResponse, HealthResponse
from src.websockets.router import router as ws_router

settings = get_settings()

_STATUS_TO_ERROR_CODE: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    500: "INTERNAL_SERVER_ERROR",
}


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(debug=settings.DEBUG)
    yield
    from src.infrastructure.database.connection import async_engine

    await async_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Collaborative Task Manager API",
        description=(
            "A **Trello/Jira-like** project & task management backend.\n\n"
            "Features:\n"
            "- JWT authentication (access + refresh tokens)\n"
            "- Multi-user with role-based permissions (Admin / Manager / Member)\n"
            "- Project & task CRUD with filtering, sorting, and pagination\n"
            "- Task comments\n"
            "- Background email notifications (simulated)\n"
            "- Real-time WebSocket notifications on task status changes\n\n"
            "Connect to WebSocket: `ws://localhost:8000/ws/notifications?token=<access_jwt>`"
        ),
        version="0.1.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Health", "description": "Health check endpoint."},
            {
                "name": "Auth",
                "description": "Register, login, and refresh JWT tokens.",
            },
            {"name": "Users", "description": "User profile — view and update."},
            {
                "name": "Projects",
                "description": "Project CRUD and member management.",
            },
            {
                "name": "Tasks",
                "description": (
                    "Task CRUD with assignment, status transitions, "
                    "filtering, sorting, and pagination."
                ),
            },
            {"name": "Comments", "description": "Comments on tasks."},
            {
                "name": "WebSocket",
                "description": (
                    "Real-time notifications. "
                    "Connect via `GET /ws/notifications?token=<access_jwt>`."
                ),
            },
        ],
        contact={"name": "API Support"},
        license_info={"name": "MIT"},
    )

    # ── Exception handlers ────────────────────────────────────────────────────

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        body = ErrorResponse(detail=str(exc), error_code="NOT_FOUND").model_dump()
        return JSONResponse(status_code=404, content=body)

    @app.exception_handler(AuthorizationError)
    async def authorization_handler(
        _request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        body = ErrorResponse(detail=str(exc), error_code="FORBIDDEN").model_dump()
        return JSONResponse(status_code=403, content=body)

    @app.exception_handler(ConflictError)
    async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
        body = ErrorResponse(detail=str(exc), error_code="CONFLICT").model_dump()
        return JSONResponse(status_code=409, content=body)

    @app.exception_handler(DomainValidationError)
    async def domain_validation_handler(
        _request: Request, exc: DomainValidationError
    ) -> JSONResponse:
        body = ErrorResponse(detail=str(exc), error_code="BAD_REQUEST").model_dump()
        return JSONResponse(status_code=400, content=body)

    @app.exception_handler(AuthenticationError)
    async def authentication_handler(
        _request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        body = ErrorResponse(detail=str(exc), error_code="UNAUTHORIZED").model_dump()
        return JSONResponse(status_code=401, content=body)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        _request: Request, exc: HTTPException
    ) -> JSONResponse:
        error_code = _STATUS_TO_ERROR_CODE.get(exc.status_code, "HTTP_ERROR")
        body = ErrorResponse(detail=exc.detail, error_code=error_code).model_dump()
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                detail=str(exc.errors()),
                error_code="VALIDATION_ERROR",
            ).model_dump(),
        )

    # ── Middleware (outermost first) ──────────────────────────────────────────
    app.middleware("http")(request_context_middleware)
    app.middleware("http")(timing_middleware)
    app.add_middleware(  # type: ignore[arg-type]
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        from sqlalchemy import text

        from src.infrastructure.database.connection import async_engine

        db_status = "unknown"
        try:
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:  # pragma: no cover
            db_status = "disconnected"

        overall = "healthy" if db_status == "connected" else "degraded"
        return HealthResponse(status=overall, version="0.1.0", database=db_status)

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(comments.router, prefix="/api/v1")
    app.include_router(ws_router)

    return app


app = create_app()
