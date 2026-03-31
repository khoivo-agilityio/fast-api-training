from datetime import datetime

from pydantic import BaseModel, Field

# ── Request schemas ───────────────────────────────────────────────────────────


class CommentCreateRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        examples=["Looks good! I'll review the PR by EOD."],
    )


class CommentUpdateRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        examples=["Updated: reviewed and approved."],
    )


# ── Response schemas ──────────────────────────────────────────────────────────


class CommentResponse(BaseModel):
    id: int
    content: str
    author_id: int
    task_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
