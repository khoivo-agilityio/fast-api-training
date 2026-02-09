"""Basic routes for items - demonstrating standard status codes."""

from fastapi import APIRouter, Body, HTTPException, Path, status
from models import Item, ItemCategory, ItemResponse

router = APIRouter(prefix="/items", tags=["Items"])


@router.post(
    "/",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_item(item: Item) -> ItemResponse:
    """
    Create a new item - Returns 201 CREATED.

    Use status_code parameter to specify custom status code.
    201 is the standard for successful resource creation.
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


@router.put(
    "/{item_id}",
    response_model=ItemResponse,
    status_code=status.HTTP_200_OK,
)
def update_item(
    item_id: int = Path(..., gt=0),
    item: Item = Body(...),
) -> ItemResponse:
    """
    Update an item - Returns 200 OK.

    200 OK is default for successful updates with response body.
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


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(item_id: int = Path(..., gt=0)) -> None:
    """
    Delete an item - Returns 204 NO CONTENT.

    204 means successful deletion with no response body.
    When using 204, don't return any data (return None).
    """
    # Simulate deletion
    pass


@router.post(
    "/{item_id}/accept",
    status_code=status.HTTP_202_ACCEPTED,
)
def accept_item(item_id: int = Path(..., gt=0)) -> dict[str, str]:
    """
    Accept an item for processing - Returns 202 ACCEPTED.

    202 indicates the request has been accepted for processing,
    but processing has not been completed (async operations).
    """
    return {
        "message": f"Item {item_id} accepted for processing",
        "status": "processing",
    }


@router.get("/{item_id}", response_model=ItemResponse)
def read_item(item_id: int = Path(..., gt=0)) -> ItemResponse:
    """
    Get item by ID - Demonstrates 404 NOT FOUND error.

    Use HTTPException to return error responses with custom status codes.
    """
    # Simulate item not found
    if item_id > 100:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )

    price = 99.99
    return ItemResponse(
        id=item_id,
        name=f"Item {item_id}",
        description="Sample item",
        price=price,
        price_with_tax=price * 1.1,
        category=ItemCategory.ELECTRONICS,
        is_offer=False,
    )
