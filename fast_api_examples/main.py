"""
FastAPI Examples - Demonstrating various parameter types and response models.
"""

from enum import Enum

from fastapi import Body, FastAPI, Header, Path, Query, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="FastAPI Examples",
    description="Comprehensive examples of FastAPI features",
    version="1.0.0",
)


class ItemCategory(str, Enum):
    """Item category enum."""

    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    BOOKS = "books"


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


class ItemResponse(BaseModel):
    """Item response model."""

    id: int
    name: str
    description: str | None = None
    price: float
    price_with_tax: float
    category: ItemCategory | None = None
    is_offer: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Laptop",
                "description": "High-performance laptop",
                "price": 999.99,
                "price_with_tax": 1099.99,
                "category": "electronics",
                "is_offer": True,
            }
        }
    }


class User(BaseModel):
    """User model."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    full_name: str | None = None
    disabled: bool = False


class UserResponse(BaseModel):
    """User response model."""

    id: int
    username: str
    email: str
    full_name: str | None = None
    disabled: bool


@app.get("/", tags=["Root"])
def read_root() -> dict[str, str]:
    """Root endpoint - health check."""
    return {"message": "Welcome to FastAPI Examples!", "status": "healthy"}


@app.get("/items/{item_id}", response_model=ItemResponse, tags=["Path Parameters"])
def read_item_by_id(
    item_id: int = Path(..., gt=0, description="The ID of the item to retrieve"),
) -> ItemResponse:
    """
    Retrieve an item by ID using path parameter.

    - **item_id**: Required path parameter (must be > 0)
    """
    # Simulate database lookup
    price = 99.99
    tax = 10.00
    return ItemResponse(
        id=item_id,
        name=f"Item {item_id}",
        description="Sample item description",
        price=price,
        price_with_tax=price + tax,
        category=ItemCategory.ELECTRONICS,
        is_offer=False,
    )


@app.get(
    "/users/{username}/items/{item_id}",
    response_model=ItemResponse,
    tags=["Path Parameters"],
)
def read_user_item(
    username: str = Path(..., min_length=3, description="Username"),
    item_id: int = Path(..., gt=0, description="Item ID"),
) -> ItemResponse:
    """
    Get a specific item for a user using multiple path parameters.

    - **username**: Required path parameter (min 3 characters)
    - **item_id**: Required path parameter (must be > 0)
    """
    price = 149.99
    return ItemResponse(
        id=item_id,
        name=f"{username}'s Item {item_id}",
        description=f"Item belonging to {username}",
        price=price,
        price_with_tax=price * 1.1,
        category=ItemCategory.BOOKS,
        is_offer=True,
    )


@app.get("/items/", tags=["Query Parameters"])
def list_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    category: ItemCategory | None = Query(None, description="Filter by category"),
    min_price: float | None = Query(None, ge=0, description="Minimum price"),
    max_price: float | None = Query(None, ge=0, description="Maximum price"),
    search: str | None = Query(None, min_length=1, description="Search term"),
    sort_by: str = Query(
        "name", regex="^(name|price|category)$", description="Sort field"
    ),
    order: str = Query("asc", regex="^(asc|desc)$", description="Sort order"),
) -> dict:
    """
    List items with various query parameters for filtering and pagination.

    - **skip**: Number of items to skip (pagination)
    - **limit**: Maximum number of items to return (1-100)
    - **category**: Filter by item category
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **search**: Search term for item name/description
    - **sort_by**: Sort by field (name, price, or category)
    - **order**: Sort order (asc or desc)
    """
    filters = {
        "skip": skip,
        "limit": limit,
        "category": category,
        "min_price": min_price,
        "max_price": max_price,
        "search": search,
        "sort_by": sort_by,
        "order": order,
    }

    # Simulate database query
    items = [
        {
            "id": i,
            "name": f"Item {i}",
            "price": 10.0 * i,
            "category": ItemCategory.ELECTRONICS,
        }
        for i in range(skip + 1, skip + limit + 1)
    ]

    return {
        "total": 100,
        "skip": skip,
        "limit": limit,
        "filters": {k: v for k, v in filters.items() if v is not None},
        "items": items,
    }


@app.get("/user/me", response_model=UserResponse, tags=["Header Parameters"])
def get_current_user(
    authorization: str = Header(..., description="Bearer token"),
    user_agent: str | None = Header(None, description="User agent string"),
    accept_language: str = Header("en-US", description="Preferred language"),
) -> UserResponse:
    """
    Get current user information using header parameters.

    - **Authorization**: Required header with bearer token
    - **User-Agent**: Optional browser/client information
    - **Accept-Language**: Language preference (default: en-US)
    """
    return UserResponse(
        id=1,
        username="john_doe",
        email="john@example.com",
        full_name="John Doe",
        disabled=False,
    )


@app.get("/debug/headers", tags=["Header Parameters"])
def read_headers(
    host: str = Header(...),
    user_agent: str = Header(...),
    accept: str = Header(...),
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    """
    Debug endpoint to display all received headers.

    - **Host**: Request host
    - **User-Agent**: Client information
    - **Accept**: Accepted content types
    - **X-Request-ID**: Optional request tracking ID
    - **X-API-Key**: Optional API key
    """
    return {
        "host": host,
        "user_agent": user_agent,
        "accept": accept,
        "x_request_id": x_request_id,
        "x_api_key": x_api_key,
    }


@app.post(
    "/items/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Request Body"],
)
def create_item(item: Item) -> ItemResponse:
    """
    Create a new item with JSON request body.

    - **item**: Item data in JSON format
    """
    item_id = 123
    price_with_tax = item.price + (item.tax or 0)

    return ItemResponse(
        id=item_id,
        name=item.name,
        description=item.description,
        price=item.price,
        price_with_tax=price_with_tax,
        category=item.category,
        is_offer=item.is_offer,
    )


@app.put("/items/{item_id}", response_model=ItemResponse, tags=["Request Body"])
def update_item(
    item_id: int = Path(..., gt=0, description="Item ID to update"),
    item: Item = Body(..., description="Updated item data"),
) -> ItemResponse:
    """
    Update an existing item using path parameter and JSON body.

    - **item_id**: ID of item to update (path parameter)
    - **item**: Updated item data (JSON body)
    """
    price_with_tax = item.price + (item.tax or 0)

    return ItemResponse(
        id=item_id,
        name=item.name,
        description=item.description,
        price=item.price,
        price_with_tax=price_with_tax,
        category=item.category,
        is_offer=item.is_offer,
    )


@app.post(
    "/users/", response_model=UserResponse, status_code=201, tags=["Request Body"]
)
def create_user(user: User) -> UserResponse:
    """
    Create a new user with JSON request body.

    - **user**: User data in JSON format
    """
    user_id = 42

    return UserResponse(
        id=user_id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled,
    )


@app.post(
    "/users/{user_id}/items/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Combined Parameters"],
)
def create_user_item(
    user_id: int = Path(..., gt=0, description="User ID"),
    item: Item = Body(..., description="Item data (request body)"),
    x_request_id: str | None = Header(None, alias="X-Request-ID"),
    notify: bool = Query(False, description="Send notification"),
) -> ItemResponse:
    """
    Create item for a user combining all parameter types.

    - **user_id**: Path parameter
    - **item**: Request body (JSON)
    - **X-Request-ID**: Header parameter
    - **notify**: Query parameter
    """
    price_with_tax = item.price + (item.tax or 0)
    item_id = 999

    return ItemResponse(
        id=item_id,
        name=f"User {user_id}'s {item.name}",
        description=item.description,
        price=item.price,
        price_with_tax=price_with_tax,
        category=item.category,
        is_offer=item.is_offer,
    )


@app.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Response Models"],
)
def delete_item(item_id: int = Path(..., gt=0)) -> None:
    """
    Delete an item (returns 204 No Content).

    - **item_id**: ID of item to delete
    """
    # Simulate deletion
    pass


@app.get(
    "/items/{item_id}/full",
    response_model=ItemResponse,
    responses={
        200: {"description": "Item found", "model": ItemResponse},
        404: {"description": "Item not found"},
        500: {"description": "Internal server error"},
    },
    tags=["Response Models"],
)
def get_item_full(item_id: int = Path(..., gt=0)) -> ItemResponse:
    """
    Get item with documented response models.

    - **item_id**: ID of item to retrieve

    Returns different status codes based on the scenario.
    """
    if item_id > 1000:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Item not found")

    price = 199.99
    return ItemResponse(
        id=item_id,
        name=f"Premium Item {item_id}",
        description="High-quality product",
        price=price,
        price_with_tax=price * 1.15,
        category=ItemCategory.ELECTRONICS,
        is_offer=True,
    )
