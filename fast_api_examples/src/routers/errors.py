"""Custom exception handlers and validation errors.

Based on FastAPI documentation:
- https://fastapi.tiangolo.com/tutorial/handling-errors/
"""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, field_validator

from models import ItemCategory

router = APIRouter(prefix="/errors", tags=["Error Handling"])


# ============================================================================
# CUSTOM EXCEPTION CLASSES
# ============================================================================


class UnicornException(Exception):
    """Custom exception for unicorn-related errors."""

    def __init__(self, name: str):
        self.name = name


# ============================================================================
# PYDANTIC MODELS WITH VALIDATION
# ============================================================================


class Item(BaseModel):
    """Item model with custom validation."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    price: float = Field(..., gt=0, description="Price must be positive")
    tax: float | None = Field(None, ge=0, le=1, description="Tax rate (0-1)")
    category: ItemCategory | None = None

    @field_validator("price")
    @classmethod
    def price_must_be_reasonable(cls, v: float) -> float:
        """Validate price is not too high."""
        if v > 1000000:
            raise ValueError("Price cannot exceed 1,000,000")
        return v

    @field_validator("name")
    @classmethod
    def name_must_not_contain_special_chars(cls, v: str) -> str:
        """Validate name doesn't contain special characters."""
        if any(char in v for char in ["<", ">", "&", ";"]):
            raise ValueError("Name contains invalid characters")
        return v


class User(BaseModel):
    """User model with email validation."""

    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    age: int = Field(..., ge=0, le=150)
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v


# ============================================================================
# BASIC HTTP EXCEPTIONS
# ============================================================================


@router.get("/items/{item_id}")
def read_item(item_id: str) -> dict:
    """
    Basic HTTPException example.

    Raises 404 if item not found.
    """
    items = {"foo": "The Foo Wrestlers"}
    if item_id not in items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    return {"item": items[item_id]}


@router.get("/items-header/{item_id}")
def read_item_header(item_id: str) -> dict:
    """
    HTTPException with custom headers.

    Useful for authentication errors with WWW-Authenticate header.
    """
    items = {"foo": "The Foo Wrestlers"}
    if item_id not in items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
            headers={"X-Error": "There goes my error"},
        )
    return {"item": items[item_id]}


# ============================================================================
# CUSTOM EXCEPTION HANDLING
# ============================================================================


@router.get("/unicorns/{name}")
def read_unicorn(name: str) -> dict:
    """
    Endpoint that raises custom exception.

    The exception handler is registered in main.py.
    """
    if name == "yolo":
        raise UnicornException(name=name)
    return {"unicorn_name": name}


# ============================================================================
# VALIDATION ERRORS WITH PYDANTIC
# ============================================================================


@router.post("/items/", status_code=status.HTTP_201_CREATED)
def create_item(item: Item) -> dict:
    """
    Create item with Pydantic validation.

    Automatic validation errors (422) if:
    - name is empty or > 100 chars
    - name contains special characters (<, >, &, ;)
    - price <= 0 or > 1,000,000
    - tax < 0 or > 1
    - category is not valid enum value
    """
    return {
        "item": item.model_dump(),
        "message": "Item created successfully",
    }


@router.post("/users/", status_code=status.HTTP_201_CREATED)
def create_user(user: User) -> dict:
    """
    Create user with complex validation.

    Automatic validation errors (422) if:
    - username < 3 or > 50 chars, or contains special chars
    - email format is invalid
    - age < 0 or > 150
    - password < 8 chars
    - password missing digit, uppercase, or lowercase letter
    """
    # Don't return password in real applications!
    return {
        "user": {
            "username": user.username,
            "email": user.email,
            "age": user.age,
        },
        "message": "User created successfully",
    }


# ============================================================================
# BUSINESS LOGIC ERRORS
# ============================================================================


@router.post("/items/{item_id}/purchase")
def purchase_item(item_id: int, quantity: int = 1) -> dict:
    """
    Demonstrates various business logic errors.
    """
    # Validation error - quantity
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be positive",
        )

    if quantity > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum quantity is 100 per order",
        )

    # Not found error
    if item_id > 1000:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found",
        )

    # Out of stock error
    if item_id == 999:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "out_of_stock",
                "message": "Item is currently out of stock",
                "item_id": item_id,
                "available_quantity": 0,
            },
        )

    # Payment required
    if item_id == 888:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Payment method required for this premium item",
        )

    return {
        "item_id": item_id,
        "quantity": quantity,
        "status": "purchased",
        "total": quantity * 99.99,
    }


# ============================================================================
# EXCEPTION HANDLERS (to be registered in main.py)
# ============================================================================


async def unicorn_exception_handler(
    request: Request, exc: UnicornException
) -> JSONResponse:
    """
    Custom exception handler for UnicornException.

    To use, add in main.py:
    app.add_exception_handler(UnicornException, unicorn_exception_handler)
    """
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Override default validation error handler.

    To use, add in main.py:
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Validation error",
            "errors": exc.errors(),
            "body": str(exc.body),
        },
    )


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> PlainTextResponse:
    """
    Override default HTTP exception handler.

    Returns plain text instead of JSON.

    To use, add in main.py:
    from fastapi.exceptions import HTTPException
    app.add_exception_handler(HTTPException, http_exception_handler)
    """
    return PlainTextResponse(
        status_code=exc.status_code,
        content=f"HTTP Error: {exc.detail}",
    )
