"""Items API router."""

from fastapi import APIRouter, HTTPException, Path, Query, status

from core.store import item_store
from models.item import ItemStatus
from schemas.item import ItemCreate, ItemResponse, ItemUpdate

router = APIRouter(prefix="/api/v1/items", tags=["Items"])


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate) -> ItemResponse:
    """
    Create a new item.

    - **name**: Item name (required, 1-100 characters)
    - **description**: Item description (optional, max 500 characters)
    - **price**: Item price (required, must be positive)
    - **status**: Item status (required: active, inactive, or archived)
    """
    created_item = item_store.create(
        name=item.name,
        description=item.description,
        price=item.price,
        status=item.status,
    )
    return ItemResponse(**created_item.to_dict())


@router.get("/", response_model=list[ItemResponse])
def get_all_items(
    status: ItemStatus | None = Query(None, description="Filter by status"),
    min_price: float | None = Query(None, ge=0, description="Minimum price filter"),
    max_price: float | None = Query(None, ge=0, description="Maximum price filter"),
) -> list[ItemResponse]:
    """
    Get all items with optional filtering.

    Query parameters:
    - **status**: Filter by item status (optional)
    - **min_price**: Minimum price (optional, >= 0)
    - **max_price**: Maximum price (optional, >= 0)
    """
    items = item_store.get_all(status=status, min_price=min_price, max_price=max_price)
    return [ItemResponse(**item.to_dict()) for item in items]


@router.get("/{item_id}", response_model=ItemResponse)
def get_item_by_id(
    item_id: int = Path(..., ge=1, description="The ID of the item to get"),
) -> ItemResponse:
    """
    Get a single item by ID.

    - **item_id**: Unique item identifier (must be >= 1)
    """
    item = item_store.get_by_id(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return ItemResponse(**item.to_dict())


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_update: ItemUpdate,
    item_id: int = Path(..., ge=1, description="The ID of the item to update"),
) -> ItemResponse:
    """
    Update an existing item.

    All fields are optional in the update request.

    - **item_id**: Unique item identifier (must be >= 1)
    - **name**: New item name (optional, 1-100 characters)
    - **description**: New item description (optional, max 500 characters)
    - **price**: New item price (optional, must be positive)
    - **status**: New item status (optional: active, inactive, or archived)
    """
    updated_item = item_store.update(
        item_id=item_id,
        name=item_update.name,
        description=item_update.description,
        price=item_update.price,
        status=item_update.status,
    )
    if updated_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return ItemResponse(**updated_item.to_dict())


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int = Path(..., ge=1, description="The ID of the item to delete"),
) -> None:
    """
    Delete an item.

    - **item_id**: Unique item identifier (must be >= 1)
    """
    deleted = item_store.delete(item_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
