"""FastAPI Exercise 2: Authenticated Database-Backed CRUD API.

This application demonstrates:
- OAuth2 JWT authentication
- SQLModel database integration
- Protected CRUD operations with authorization
- User ownership of resources
"""

from contextlib import asynccontextmanager

from database import create_db_and_tables
from fastapi import FastAPI
from routers import auth, items


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create database tables
    create_db_and_tables()
    yield
    # Shutdown: (cleanup if needed)


app = FastAPI(
    title="FastAPI Exercise 2",
    description="Authenticated, database-backed CRUD API with protected routes",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(auth.router)
app.include_router(items.router)


@app.get("/")
def read_root() -> dict:
    """Root endpoint - API information."""
    return {
        "message": "FastAPI Exercise 2: Authenticated CRUD API",
        "docs": "/docs",
        "endpoints": {
            "register": "POST /register",
            "login": "POST /token",
            "current_user": "GET /users/me",
            "items": "/items (requires authentication)",
        },
    }


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}
