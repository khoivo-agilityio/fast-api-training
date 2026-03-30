from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_current_user, get_project_service
from src.domain.entities.user import UserEntity
from src.domain.services.project_service import ProjectService
from src.schemas.common import PaginatedResponse, PaginationParams
from src.schemas.project import (
    AddMemberRequest,
    ProjectCreateRequest,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdateRequest,
    UpdateMemberRoleRequest,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreateRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    project = await service.create_project(
        name=body.name,
        owner_id=current_user.id,
        description=body.description,
    )
    return ProjectResponse.model_validate(project)


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    pagination: PaginationParams = Depends(),
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> PaginatedResponse[ProjectResponse]:
    items, total = await service.list_projects(
        current_user.id, limit=pagination.limit, offset=pagination.offset
    )
    return PaginatedResponse(
        items=[ProjectResponse.model_validate(p) for p in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    _current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    project = await service.get_project(project_id)
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    body: ProjectUpdateRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    updates = body.model_dump(exclude_unset=True)
    project = await service.update_project(
        project_id=project_id,
        requester_id=current_user.id,
        **updates,
    )
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> None:
    await service.delete_project(
        project_id=project_id,
        requester_id=current_user.id,
    )


# ── Members ───────────────────────────────────────────────────────────────────


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    project_id: int,
    body: AddMemberRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectMemberResponse:
    member = await service.add_member(
        project_id=project_id,
        requester_id=current_user.id,
        user_id=body.user_id,
        role=body.role,
    )
    return ProjectMemberResponse.model_validate(member)


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_members(
    project_id: int,
    _current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> list[ProjectMemberResponse]:
    members = await service.list_members(project_id)
    return [ProjectMemberResponse.model_validate(m) for m in members]


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_member_role(
    project_id: int,
    user_id: int,
    body: UpdateMemberRoleRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectMemberResponse:
    member = await service.update_member_role(
        project_id=project_id,
        requester_id=current_user.id,
        user_id=user_id,
        role=body.role,
    )
    return ProjectMemberResponse.model_validate(member)


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    project_id: int,
    user_id: int,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> None:
    await service.remove_member(
        project_id=project_id,
        requester_id=current_user.id,
        user_id=user_id,
    )
