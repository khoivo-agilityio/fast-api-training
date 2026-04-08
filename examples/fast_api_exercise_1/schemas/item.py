"""Pydantic schemas for Item API."""

from datetime import datetime

from models.item import ItemStatus
from pydantic import BaseModel, Field


class ItemBase(BaseModel):
    """Base item schema with shared fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: str | None = Field(
        None, max_length=500, description="Item description"
    )
    price: float = Field(..., gt=0, description="Item price (must be positive)")
    status: ItemStatus = Field(..., description="Item status")


class ItemCreate(ItemBase):
    """Schema for creating a new item."""

    pass


class ItemUpdate(BaseModel):
    """Schema for updating an existing item (all fields optional)."""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="Item name"
    )
    description: str | None = Field(
        None, max_length=500, description="Item description"
    )
    price: float | None = Field(None, gt=0, description="Item price (must be positive)")
    status: ItemStatus | None = Field(None, description="Item status")


class ItemResponse(ItemBase):
    """Schema for item response with id and timestamps."""

    id: int = Field(..., description="Unique item identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True
