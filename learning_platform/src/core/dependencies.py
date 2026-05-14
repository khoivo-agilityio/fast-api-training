"""Storage module FastAPI dependency."""

from src.core.service import StorageService


def get_storage_service() -> StorageService:
    """Return a StorageService instance (stateless — no DB needed)."""
    return StorageService()
