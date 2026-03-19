"""FastAPI dependency injection — DB session, services, current user."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.core.security import extract_token_subject
from src.domain.entities.user import User
from src.domain.services.auth_service import AuthService
from src.domain.services.task_service import TaskService
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories import (
    SQLAlchemyTaskRepository,
    SQLAlchemyUserRepository,
)

# ── OAuth2 scheme ──────────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ── DB session ─────────────────────────────────────────────────────────────────
DbSession = Annotated[Session, Depends(get_db)]


# ── Service factories ──────────────────────────────────────────────────────────
def get_auth_service(db: DbSession) -> AuthService:
    """Provide an AuthService backed by the SQLAlchemy user repository."""
    return AuthService(user_repository=SQLAlchemyUserRepository(db))


def get_task_service(db: DbSession) -> TaskService:
    """Provide a TaskService backed by the SQLAlchemy task repository."""
    return TaskService(task_repository=SQLAlchemyTaskRepository(db))


# ── Typed dependency aliases ───────────────────────────────────────────────────
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


# ── Current user ───────────────────────────────────────────────────────────────
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthServiceDep,
) -> User:
    """
    Decode the Bearer JWT, look up the user, and return the User entity.

    Raises HTTP 401 if the token is missing, invalid, expired, or the user
    no longer exists / is inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    username = extract_token_subject(token)
    if username is None:
        raise credentials_exception

    user = auth_service.user_repository.get_by_username(username)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
