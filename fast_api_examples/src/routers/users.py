"""User routes - demonstrating error handling and validation."""

from fastapi import APIRouter, HTTPException, Path, status
from src.models import User, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{username}", response_model=UserResponse)
def read_user(username: str = Path(..., min_length=3)) -> UserResponse:
    """
    Get user by username - Demonstrates multiple error scenarios.
    """
    # Check for invalid characters
    if not username.isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must contain only alphanumeric characters",
        )

    # Check for reserved usernames
    if username.lower() in ["admin", "root", "system"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Username '{username}' is reserved and cannot be accessed",
        )

    # Simulate user not found
    if username == "notfound":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found",
        )

    return UserResponse(
        id=1,
        username=username,
        email=f"{username}@example.com",
        full_name=username.title(),
        disabled=False,
    )


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: User) -> UserResponse:
    """
    Create user - Pydantic automatically returns 422 for validation errors.

    FastAPI automatically handles validation errors and returns:
    - 422 UNPROCESSABLE ENTITY for invalid data
    - Detailed error information about what went wrong
    """
    # Simulate username already exists
    if user.username == "admin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    return UserResponse(
        id=42,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        disabled=user.disabled,
    )
