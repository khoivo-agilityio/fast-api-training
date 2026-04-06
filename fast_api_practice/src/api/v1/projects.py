from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from src.api.dependencies import get_current_user, get_project_service
from src.domain.entities.user import UserEntity
from src.domain.services.project_service import ProjectService
from src.infrastructure.background import simulate_project_created_email
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
    background_tasks: BackgroundTasks,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    try:
        project = await service.create_project(
            name=body.name,
            owner_id=current_user.id,
            description=body.description,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    background_tasks.add_task(
        simulate_project_created_email,
        project_id=project.id,
        project_name=project.name,
        owner_id=current_user.id,
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
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    try:
        project = await service.get_project(project_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    try:
        await service.require_member(project_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    body: ProjectUpdateRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    updates = body.model_dump(exclude_unset=True)
    try:
        project = await service.update_project(
            project_id=project_id,
            requester_id=current_user.id,
            **updates,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> None:
    try:
        await service.delete_project(
            project_id=project_id,
            requester_id=current_user.id,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


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
    try:
        member = await service.add_member(
            project_id=project_id,
            requester_id=current_user.id,
            user_id=body.user_id,
            role=body.role,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return ProjectMemberResponse.model_validate(member)


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_members(
    project_id: int,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> list[ProjectMemberResponse]:
    try:
        await service.require_member(project_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    try:
        members = await service.list_members(project_id)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    return [ProjectMemberResponse.model_validate(m) for m in members]


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_member_role(
    project_id: int,
    user_id: int,
    body: UpdateMemberRoleRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectMemberResponse:
    try:
        member = await service.update_member_role(
            project_id=project_id,
            requester_id=current_user.id,
            user_id=user_id,
            role=body.role,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
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
    try:
        await service.remove_member(
            project_id=project_id,
            requester_id=current_user.id,
            user_id=user_id,
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
