from abc import ABC, abstractmethod
from typing import Any


class BaseRepository(ABC):
    """Generic repository interface."""

    @abstractmethod
    async def get_by_id(self, id: int) -> Any | None: ...
