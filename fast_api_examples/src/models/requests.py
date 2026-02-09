"""Request models for FastAPI examples."""

from pydantic import BaseModel, Field, field_validator

from .enums import ItemCategory


class Item(BaseModel):
    """Item model for requests."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: str | None = Field(
        None, max_length=500, description="Item description"
    )
    price: float = Field(..., gt=0, description="Item price (must be positive)")
    tax: float | None = Field(None, ge=0, description="Tax amount")
    category: ItemCategory | None = Field(None, description="Item category")
    is_offer: bool = False

    @field_validator("price")
    @classmethod
    def price_must_be_reasonable(cls, v: float) -> float:
        """Validate that price is reasonable."""
        if v > 1000000:
            raise ValueError("Price too high")
        return v


class User(BaseModel):
    """User model."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    full_name: str | None = None
    disabled: bool = False
