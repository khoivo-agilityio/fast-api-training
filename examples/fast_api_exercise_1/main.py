"""FastAPI Exercise 1: In-Memory CRUD API.

This application demonstrates:
- Strong data validation using Pydantic
- Clear separation of concerns (models, schemas, routes)
- Automatically generated interactive API documentation
"""

from apis.items import router as items_router
from fastapi import FastAPI

# Initialize FastAPI application
app = FastAPI(
    title="FastAPI Exercise 1: In-Memory CRUD API",
    description="A simple CRUD API for managing items with in-memory storage",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include routers
app.include_router(items_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
