"""Routers package for FastAPI examples."""

from .advanced import router as advanced_router
from .errors import router as errors_router
from .items import router as items_router
from .security import router as security_router
from .serialization import router as serialization_router
from .users import router as users_router
from .validation import router as validation_router

__all__ = [
    "items_router",
    "users_router",
    "security_router",
    "advanced_router",
    "validation_router",
    "serialization_router",
    "errors_router",
]
