from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1 import auth, users
from src.schemas.common import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        return HealthResponse(status="healthy", version="0.1.0")

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")

    return app


app = create_app()
