from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import request_context_middleware, timing_middleware
from src.api.v1 import auth, comments, projects, tasks, users
from src.core.config import get_settings
from src.infrastructure.logging.setup import configure_logging
from src.schemas.common import HealthResponse

settings = get_settings()


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
