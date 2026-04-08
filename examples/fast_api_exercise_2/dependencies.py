"""Dependency injection helpers."""

from typing import Annotated

from auth import get_current_active_user
from database import get_session
from fastapi import Depends
from models import User
from sqlmodel import Session

# Type aliases for cleaner code
SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_current_active_user)]
