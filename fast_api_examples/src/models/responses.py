"""Response models for FastAPI examples."""

from pydantic import BaseModel

from .enums import ItemCategory


class ItemResponse(BaseModel):
    """Item response model."""

    id: int
    name: str
    description: str | None = None
    price: float
    price_with_tax: float
    category: ItemCategory | None = None
    is_offer: bool


class UserResponse(BaseModel):
    """User response model."""

    id: int
    username: str
    email: str
    full_name: str | None = None
    disabled: bool


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    message: str
    details: dict | None = None
