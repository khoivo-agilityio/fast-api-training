import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import decode_token
from src.domain.entities.user import UserEntity
from src.domain.services.comment_service import CommentService
from src.domain.services.project_service import ProjectService
from src.domain.services.task_service import TaskService
from src.domain.services.user_service import UserService
from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.repositories import (
    SQLAlchemyCommentRepository,
    SQLAlchemyProjectRepository,
    SQLAlchemyTaskRepository,
    SQLAlchemyUserRepository,
)

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> UserEntity:
    """Extract and validate JWT, return UserEntity."""
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = int(payload["sub"])
    repo = SQLAlchemyUserRepository(session)
    user = await repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    return user


async def get_project_service(
    session: AsyncSession = Depends(get_async_session),
) -> ProjectService:
    return ProjectService(
        project_repo=SQLAlchemyProjectRepository(session),
        user_repo=SQLAlchemyUserRepository(session),
    )


async def get_task_service(
    session: AsyncSession = Depends(get_async_session),
) -> TaskService:
    return TaskService(
        task_repo=SQLAlchemyTaskRepository(session),
        project_repo=SQLAlchemyProjectRepository(session),
    )


async def get_comment_service(
    session: AsyncSession = Depends(get_async_session),
) -> CommentService:
    return CommentService(
        comment_repo=SQLAlchemyCommentRepository(session),
        task_repo=SQLAlchemyTaskRepository(session),
        project_repo=SQLAlchemyProjectRepository(session),
    )


async def get_user_service(
    session: AsyncSession = Depends(get_async_session),
) -> UserService:
    return UserService(user_repo=SQLAlchemyUserRepository(session))
