"""Authentication routes."""

from datetime import timedelta
from typing import Annotated

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    get_user_by_username,
)
from background_tasks import log_authentication, send_welcome_email
from database import get_session
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from models import User
from schemas import Token, UserCreate, UserResponse
from sqlmodel import Session

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_session)],
) -> User:
    """
    Register a new user.

    Background tasks:
    - Send welcome email
    - Log registration
    """
    # Check if username already exists
    existing_user = get_user_by_username(session, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    # Add background tasks
    background_tasks.add_task(
        send_welcome_email, email=db_user.email, username=db_user.username
    )
    background_tasks.add_task(
        log_authentication,
        username=db_user.username,
        success=True,
        ip_address="register",
    )

    return db_user


@router.post("/token", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_session)],
    request: Request,
) -> dict:
    """
    OAuth2 compatible token login.

    Background tasks:
    - Log authentication attempt
    """
    user = authenticate_user(session, form_data.username, form_data.password)

    # Get client IP
    client_ip = request.client.host if request.client else "unknown"

    if not user:
        # Log failed authentication
        background_tasks.add_task(
            log_authentication,
            username=form_data.username,
            success=False,
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log successful authentication
    background_tasks.add_task(
        log_authentication,
        username=user.username,
        success=True,
        ip_address=client_ip,
    )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserResponse)
def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Get current authenticated user information."""
    return current_user
