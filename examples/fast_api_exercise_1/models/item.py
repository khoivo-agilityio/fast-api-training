"""Item model definition."""

from datetime import datetime
from enum import Enum


class ItemStatus(str, Enum):
    """Item status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Item:
    """In-memory item model."""

    def __init__(
        self,
        id: int,
        name: str,
        price: float,
        status: ItemStatus,
        description: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.status = status
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        price: float | None = None,
        status: ItemStatus | None = None,
    ) -> None:
        """Update item fields."""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if price is not None:
            self.price = price
        if status is not None:
            self.status = status
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert item to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
