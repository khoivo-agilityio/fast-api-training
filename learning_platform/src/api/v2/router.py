"""
API v2 Router — placeholder for future v2 endpoints.

Add new v2 endpoints here. Endpoints not yet re-versioned can be
forwarded from v1 or simply not included until ready.
"""

from fastapi import APIRouter

v2_router = APIRouter(prefix="/api/v2")


# Example: when you add a v2 endpoint, register it here:
# from src.courses.router_v2 import router as courses_v2_router
# v2_router.include_router(courses_v2_router)


@v2_router.get("/health", tags=["system"])
async def v2_health() -> dict[str, str]:
    """V2 health check — confirms v2 routing is active."""
    return {"status": "healthy", "version": "v2"}
