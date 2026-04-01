from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.entities.project_member import ProjectMemberRole


class ProjectCreateRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, examples=["My Awesome Project"]
    )
    description: str | None = Field(
        None, max_length=2000, examples=["A project for tracking tasks and milestones"]
    )


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(
        None, min_length=1, max_length=100, examples=["Renamed Project"]
    )
    description: str | None = Field(
        None, max_length=2000, examples=["Updated project description"]
    )


class AddMemberRequest(BaseModel):
    user_id: int = Field(..., examples=[42])
    role: ProjectMemberRole = Field(ProjectMemberRole.MEMBER, examples=["member"])


class UpdateMemberRoleRequest(BaseModel):
    role: ProjectMemberRole


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectMemberResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    role: ProjectMemberRole
    joined_at: datetime

    model_config = {"from_attributes": True}
