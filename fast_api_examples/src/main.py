"""
FastAPI Examples - Response Status Codes and Error Handling

This is the main application file that imports and registers all routers.
Models and route handlers are organized in separate modules for better maintainability.
"""

from fastapi import FastAPI

from routers import advanced_router, items_router, security_router, users_router

app = FastAPI(
    title="FastAPI Examples",
    description="Comprehensive examples of FastAPI features including status codes, error handling, and best practices",
    version="1.0.0",
)

# Register routers
app.include_router(items_router)
app.include_router(users_router)
app.include_router(security_router)
app.include_router(advanced_router)


@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    """
    Root endpoint - Default status code 200 OK.

    FastAPI automatically returns 200 OK for successful GET requests.
    """
    return {
        "message": "Welcome to FastAPI Examples!",
        "status": "healthy",
        "docs": "/docs",
        "redoc": "/redoc",
    }
