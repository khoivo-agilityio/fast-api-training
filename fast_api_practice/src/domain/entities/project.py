from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProjectEntity:
    id: int
    name: str
    description: str | None
    owner_id: int
    created_at: datetime
    updated_at: datetime
