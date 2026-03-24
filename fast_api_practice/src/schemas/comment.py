from datetime import datetime

from pydantic import BaseModel, Field

# ── Request schemas ───────────────────────────────────────────────────────────


class CommentCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


class CommentUpdateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


# ── Response schemas ──────────────────────────────────────────────────────────


class CommentResponse(BaseModel):
    id: int
    content: str
    author_id: int
    task_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
