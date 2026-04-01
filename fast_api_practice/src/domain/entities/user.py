from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserEntity:
    id: int
    username: str
    email: str
    hashed_password: str
    full_name: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
