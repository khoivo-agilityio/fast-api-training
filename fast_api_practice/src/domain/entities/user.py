from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"


@dataclass
class UserEntity:
    id: int
    username: str
    email: str
    hashed_password: str
    full_name: str | None
    is_active: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime
