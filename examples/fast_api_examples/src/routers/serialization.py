"""Output serialization and response models examples.

Demonstrates how FastAPI handles response serialization with Pydantic models.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, Field, field_serializer
from src.models import ItemCategory

router = APIRouter(prefix="/serialization", tags=["Serialization"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================


class UserBase(BaseModel):
    """Base user model with common fields."""

    username: str
    email: str
    full_name: str | None = None


class UserIn(UserBase):
    """User model for input (includes password)."""

    password: str


class UserOut(UserBase):
    """User model for output (excludes password)."""

    id: int
    is_active: bool = True


class UserInDB(UserBase):
    """User model in database (includes hashed password)."""

    id: int
    hashed_password: str
    is_active: bool = True


# ============================================================================
# ITEM MODELS WITH SERIALIZATION
# ============================================================================


class ItemBase(BaseModel):
    """Base item model."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(..., gt=0)
    tax: float | None = None
    category: ItemCategory | None = None


class ItemCreate(ItemBase):
    """Item model for creation."""

    pass


class ItemResponse(ItemBase):
    """Item model for response with computed fields."""

    id: int
    price_with_tax: float
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: datetime, _info: Any) -> str:
        """Serialize datetime to ISO format string."""
        return dt.isoformat()


class ItemDetail(ItemResponse):
    """Detailed item model with additional fields."""

    views: int = 0
    likes: int = 0
    tags: list[str] = Field(default_factory=list)


# ============================================================================
# RESPONSE MODEL EXAMPLES
# ============================================================================


@router.post("/users/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserIn) -> Any:
    """
    Create user - password is excluded from response.

    Input: UserIn (with password)
    Output: UserOut (without password)

    FastAPI automatically filters the response based on response_model.
    """
    # Simulate password hashing
    user_in_db = UserInDB(
        id=1,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=f"hashed_{user.password}",
        is_active=True,
    )

    # Return full object, FastAPI will filter based on UserOut
    return user_in_db


@router.get("/users/{user_id}", response_model=UserOut)
def read_user(user_id: int) -> Any:
    """
    Get user - returns only public fields.
    """
    # Simulate database retrieval
    user_in_db = UserInDB(
        id=user_id,
        username=f"user{user_id}",
        email=f"user{user_id}@example.com",
        full_name=f"User {user_id}",
        hashed_password="super_secret_hash",
        is_active=True,
    )

    return user_in_db


# ============================================================================
# RESPONSE MODEL WITH COMPUTED FIELDS
# ============================================================================


@router.post(
    "/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED
)
def create_item(item: ItemCreate) -> dict:
    """
    Create item - response includes computed fields.

    The response_model automatically:
    - Adds computed fields (price_with_tax, created_at, updated_at)
    - Serializes datetime fields to ISO format
    """
    # Simulate database save with additional fields
    return {
        "id": 1,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "tax": item.tax,
        "category": item.category,
        "price_with_tax": item.price + (item.price * (item.tax or 0)),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@router.get("/items/{item_id}", response_model=ItemDetail)
def read_item(item_id: int) -> dict:
    """
    Get item with detailed information.
    """
    return {
        "id": item_id,
        "name": f"Item {item_id}",
        "description": "Sample item description",
        "price": 99.99,
        "tax": 0.1,
        "category": ItemCategory.ELECTRONICS,
        "price_with_tax": 109.99,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "views": 1234,
        "likes": 56,
        "tags": ["popular", "trending", "new"],
    }


# ============================================================================
# MULTIPLE RESPONSE MODELS
# ============================================================================


@router.get("/items/", response_model=list[ItemResponse])
def list_items() -> list[dict]:
    """
    List all items - returns list of ItemResponse.
    """
    now = datetime.now()
    return [
        {
            "id": 1,
            "name": "Item 1",
            "description": "First item",
            "price": 50.0,
            "tax": 0.1,
            "category": ItemCategory.ELECTRONICS,
            "price_with_tax": 55.0,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": 2,
            "name": "Item 2",
            "description": "Second item",
            "price": 100.0,
            "tax": 0.15,
            "category": ItemCategory.BOOKS,
            "price_with_tax": 115.0,
            "created_at": now,
            "updated_at": now,
        },
    ]


# ============================================================================
# RESPONSE MODEL WITH UNION TYPES
# ============================================================================


class SuccessResponse(BaseModel):
    """Success response model."""

    success: bool = True
    message: str
    data: dict | None = None


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: str
    details: dict | None = None


@router.post("/items/{item_id}/process", response_model=SuccessResponse | ErrorResponse)
def process_item(item_id: int, simulate_error: bool = False) -> dict:
    """
    Process item - can return success or error response.
    """
    if simulate_error:
        return {
            "success": False,
            "error": "Processing failed",
            "details": {"item_id": item_id, "reason": "Simulated error"},
        }

    return {
        "success": True,
        "message": "Item processed successfully",
        "data": {"item_id": item_id, "status": "completed"},
    }


# ============================================================================
# RESPONSE MODEL CONFIGURATION
# ============================================================================


class ItemSummary(BaseModel):
    """Item summary with model configuration."""

    name: str
    price: float

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Sample Item",
                    "price": 99.99,
                }
            ]
        }
    }


@router.get("/items/summary/{item_id}", response_model=ItemSummary)
def read_item_summary(item_id: int) -> dict:
    """
    Get item summary - uses schema examples in OpenAPI docs.
    """
    return {
        "name": f"Item {item_id}",
        "price": 99.99,
    }


# ============================================================================
# RESPONSE WITHOUT MODEL (DICT)
# ============================================================================


@router.get("/items/raw/{item_id}")
def read_item_raw(item_id: int) -> dict[str, Any]:
    """
    Return raw dict without response model.

    No validation or serialization is performed.
    Use this when you need maximum flexibility.
    """
    return {
        "item_id": item_id,
        "raw_data": "This is not validated",
        "nested": {
            "key": "value",
            "number": 123,
        },
        "timestamp": datetime.now().isoformat(),
    }
