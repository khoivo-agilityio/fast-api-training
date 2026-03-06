"""
FastAPI Examples - Response Status Codes and Error Handling

This is the main application file that imports and registers all routers.
Models and route handlers are organized in separate modules for better maintainability.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from routers import (
    advanced_router,
    errors_router,
    items_router,
    security_router,
    serialization_router,
    users_router,
    validation_router,
)
from routers.errors import UnicornException

app = FastAPI(
    title="FastAPI Examples",
    description="Comprehensive examples of FastAPI features including status codes, error handling, and best practices",
    version="1.0.0",
)


# ============================================================================
# CUSTOM EXCEPTION HANDLERS
# ============================================================================


@app.exception_handler(UnicornException)
async def unicorn_exception_handler(
    request: Request, exc: UnicornException
) -> JSONResponse:
    """Handle custom UnicornException."""
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Override default validation error handler to provide custom format.
    """
    return JSONResponse(
        status_code=422,
        content={
            "message": "Validation error occurred",
            "errors": exc.errors(),
            "body": str(exc.body) if exc.body else None,
        },
    )


# ============================================================================
# REGISTER ROUTERS
# ============================================================================

app.include_router(items_router)
app.include_router(users_router)
app.include_router(security_router)
app.include_router(advanced_router)
app.include_router(validation_router)
app.include_router(serialization_router)
app.include_router(errors_router)


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
