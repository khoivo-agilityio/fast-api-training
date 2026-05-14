"""
Shared Pagination Utilities.

Usage in routers:
    @router.get("/items")
    async def list_items(pagination: PaginationParams = Depends()):
        ...
"""

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    limit: int = Field(20, ge=1, le=100, description="Items per page (max 100)")
    offset: int = Field(0, ge=0, description="Number of items to skip")
