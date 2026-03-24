from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ProjectMemberRole(StrEnum):
    MANAGER = "manager"
    MEMBER = "member"


@dataclass
class ProjectMemberEntity:
    id: int
    project_id: int
    user_id: int
    role: ProjectMemberRole
    joined_at: datetime
