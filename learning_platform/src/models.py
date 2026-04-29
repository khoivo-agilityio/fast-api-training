"""Re-export all ORM models so Alembic autogenerate sees every table.

Import this module in alembic/env.py to register all models with Base.metadata.
"""

from src.users.models import User  # noqa: F401

__all__ = [
    "User",
]
