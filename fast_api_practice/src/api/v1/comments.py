from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_comment_service, get_current_user
from src.domain.entities.user import UserEntity
from src.domain.services.comment_service import CommentService
from src.schemas.comment import (
    CommentCreateRequest,
    CommentResponse,
    CommentUpdateRequest,
)
from src.schemas.common import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/tasks/{task_id}/comments", tags=["Comments"])


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: int,
    body: CommentCreateRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    comment = await service.create_comment(
        task_id=task_id,
        author_id=current_user.id,
        content=body.content,
    )
    return CommentResponse.model_validate(comment)


@router.get("", response_model=PaginatedResponse[CommentResponse])
async def list_comments(
    task_id: int,
    pagination: PaginationParams = Depends(),
    current_user: UserEntity = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> PaginatedResponse[CommentResponse]:
    items, total = await service.list_comments(
        task_id=task_id,
        requester_id=current_user.id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return PaginatedResponse(
        items=[CommentResponse.model_validate(c) for c in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    task_id: int,
    comment_id: int,
    body: CommentUpdateRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    comment = await service.update_comment(
        comment_id=comment_id,
        requester_id=current_user.id,
        content=body.content,
    )
    return CommentResponse.model_validate(comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    task_id: int,
    comment_id: int,
    current_user: UserEntity = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> None:
    await service.delete_comment(comment_id=comment_id, requester_id=current_user.id)
