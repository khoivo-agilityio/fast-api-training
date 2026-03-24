from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.entities.project_member import ProjectMemberRole


class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=2000)


class AddMemberRequest(BaseModel):
    user_id: int
    role: ProjectMemberRole = ProjectMemberRole.MEMBER


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
