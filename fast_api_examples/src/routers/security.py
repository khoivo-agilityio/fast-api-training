"""Security and authentication routes - demonstrating auth errors."""

from fastapi import APIRouter, Header, HTTPException, Path, Query, status

router = APIRouter(tags=["Security"])


@router.get("/items/{item_id}/secure")
def read_secure_item(
    item_id: int = Path(..., gt=0),
    x_token: str | None = Header(None, alias="X-Token"),
) -> dict:
    """
    Demonstrates authentication error with custom headers.

    401 UNAUTHORIZED - Missing or invalid authentication.
    Include WWW-Authenticate header for proper HTTP auth.
    """
    if not x_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if x_token != "secret-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"item_id": item_id, "owner": "authenticated_user"}


@router.post("/items/{item_id}/purchase")
def purchase_item(
    item_id: int = Path(..., gt=0),
    quantity: int = Query(..., ge=1, le=100),
) -> dict:
    """
    Demonstrates business logic errors with detailed information.
    """
    # Simulate out of stock
    if quantity > 50:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "insufficient_stock",
                "message": "Not enough items in stock",
                "available": 50,
                "requested": quantity,
            },
        )

    # Simulate payment required
    if item_id == 999:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment method required for this item",
        )

    return {
        "item_id": item_id,
        "quantity": quantity,
        "status": "purchased",
        "total": quantity * 99.99,
    }


@router.get("/api/data")
def get_data(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    """
    Demonstrates rate limiting with 429 TOO MANY REQUESTS.
    """
    # Simulate rate limit exceeded
    # In real app, you'd check against a rate limiter (Redis, etc.)
    if x_api_key == "rate-limited":
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 100 requests per hour.",
            headers={"Retry-After": "3600"},
        )

    return {"data": "sample data", "timestamp": "2026-02-09T10:30:00Z"}
