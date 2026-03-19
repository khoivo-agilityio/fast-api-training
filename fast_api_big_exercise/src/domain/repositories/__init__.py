"""Repository interfaces for domain layer.

This package contains abstract base classes (interfaces) that define
contracts for data access operations.

These interfaces allow the domain layer to be independent of infrastructure
concerns (database, ORM, etc.).
"""

from src.domain.repositories.task_repository import TaskRepository
from src.domain.repositories.user_repository import UserRepository

__all__ = [
    "UserRepository",
    "TaskRepository",
]
