"""Protected CRUD routes for items."""

from datetime import datetime
from typing import Annotated

from auth import get_current_active_user
from database import get_session
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models import Item, ItemStatus, User
from schemas import ItemCreate, ItemResponse, ItemUpdate
from sqlmodel import Session, select

router = APIRouter(prefix="/items", tags=["Items (Protected)"])


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Item:
    """
    Create a new item (requires authentication).

    The item will be owned by the authenticated user.
    """
    db_item = Item(
        **item_data.model_dump(),
        owner_id=current_user.id,
    )

    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    return db_item


@router.get("/", response_model=list[ItemResponse])
def list_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: ItemStatus | None = Query(None, alias="status"),
    my_items_only: bool = Query(False, description="Show only my items"),
) -> list[Item]:
    """
    List items (requires authentication).

    - **skip**: Number of items to skip (pagination)
    - **limit**: Max items to return (1-100)
    - **status**: Filter by status
    - **my_items_only**: If true, only show authenticated user's items
    """
    statement = select(Item)

    # Filter by owner if requested
    if my_items_only:
        statement = statement.where(Item.owner_id == current_user.id)

    # Filter by status if provided
    if status_filter:
        statement = statement.where(Item.status == status_filter)

    # Apply pagination
    statement = statement.offset(skip).limit(limit)

    items = session.exec(statement).all()
    return list(items)  # Convert Sequence to list


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Item:
    """
    Get a specific item by ID (requires authentication).

    Users can only view their own items or published items.
    """
    item = session.get(Item, item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )

    # Authorization: Users can only see their own items or published items
    if item.owner_id != current_user.id and item.status != ItemStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this item",
        )

    return item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_data: ItemUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Item:
    """
    Update an item (requires authentication).

    Users can only update their own items.
    """
    db_item = session.get(Item, item_id)

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )

    # Authorization: Users can only update their own items
    if db_item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this item",
        )

    # Update only provided fields
    update_data = item_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db_item.updated_at = datetime.utcnow()

    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    """
    Delete an item (requires authentication).

    Users can only delete their own items.
    """
    db_item = session.get(Item, item_id)

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )

    # Authorization: Users can only delete their own items
    if db_item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this item",
        )

    session.delete(db_item)
    session.commit()
