from dataclasses import dataclass
from datetime import datetime


@dataclass
class CommentEntity:
    id: int
    content: str
    author_id: int
    task_id: int
    created_at: datetime
    updated_at: datetime
