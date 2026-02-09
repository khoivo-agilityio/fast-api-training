"""Advanced routes - demonstrating custom responses and documentation."""

from fastapi import APIRouter, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse
from models import ErrorResponse, ItemCategory, ItemResponse

router = APIRouter(tags=["Advanced"])


@router.get(
    "/items/{item_id}/documented",
    response_model=ItemResponse,
    responses={
        200: {
            "description": "Successful response",
            "model": ItemResponse,
        },
        400: {
            "description": "Bad request - Invalid item ID",
            "model": ErrorResponse,
        },
        404: {
            "description": "Item not found",
            "model": ErrorResponse,
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse,
        },
    },
)
def get_item_documented(item_id: int = Path(..., gt=0)) -> ItemResponse:
    """
    Get item with fully documented possible responses.

    This endpoint documents all possible status codes in OpenAPI/Swagger.
    Useful for API consumers to understand all possible outcomes.
    """
    if item_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item ID must be positive",
        )

    if item_id > 1000:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )

    price = 199.99
    return ItemResponse(
        id=item_id,
        name=f"Item {item_id}",
        description="Premium product",
        price=price,
        price_with_tax=price * 1.15,
        category=ItemCategory.ELECTRONICS,
        is_offer=True,
    )


@router.post(
    "/items/{item_id}/process",
    responses={
        202: {
            "description": "Request accepted for processing",
            "content": {
                "application/json": {
                    "example": {
                        "status": "processing",
                        "job_id": "abc-123",
                    }
                }
            },
        },
        200: {
            "description": "Request processed immediately",
            "content": {
                "application/json": {
                    "example": {
                        "status": "completed",
                        "result": "success",
                    }
                }
            },
        },
        400: {"description": "Invalid request"},
        503: {"description": "Service temporarily unavailable"},
    },
)
def process_item(
    item_id: int = Path(..., gt=0),
    async_processing: bool = Query(False, description="Use async processing"),
) -> JSONResponse:
    """
    Process an item - returns different status codes based on processing mode.

    Returns:
    - 202 ACCEPTED if async processing is requested
    - 200 OK if processed immediately
    - 400 BAD REQUEST if item_id is invalid
    - 503 SERVICE UNAVAILABLE if system is overloaded
    """
    # Simulate system overload
    if item_id > 10000:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "service_unavailable",
                "message": "System is currently overloaded. Please try again later.",
                "retry_after": 60,
            },
            headers={"Retry-After": "60"},
        )

    # Async processing
    if async_processing:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "processing",
                "job_id": f"job-{item_id}-async",
                "message": "Item accepted for asynchronous processing",
            },
        )

    # Immediate processing
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "completed",
            "item_id": item_id,
            "result": "success",
            "message": "Item processed successfully",
        },
    )
