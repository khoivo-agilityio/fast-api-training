from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.middleware import request_context_middleware, timing_middleware
from src.api.v1 import auth, comments, projects, tasks, users
from src.core.config import get_settings
from src.infrastructure.logging.setup import configure_logging
from src.schemas.common import ErrorResponse, HealthResponse

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
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging(debug=settings.DEBUG)
    yield
    from src.infrastructure.database.connection import async_engine

    await async_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Collaborative Task Manager API",
        description="A Trello/Jira-like project & task management backend",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        error_code = _STATUS_TO_ERROR_CODE.get(exc.status_code, "HTTP_ERROR")
        body = ErrorResponse(detail=exc.detail, error_code=error_code).model_dump()
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
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
        return HealthResponse(status="healthy", version="0.1.0")

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(comments.router, prefix="/api/v1")

    return app


app = create_app()
