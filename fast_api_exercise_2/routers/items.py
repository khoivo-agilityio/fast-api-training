"""Protected CRUD routes for items."""

from datetime import datetime
from typing import Annotated

from auth import get_current_active_user
from background_tasks import (
    generate_user_stats,
    log_item_activity,
    process_item_data,
    send_item_notification,
)
from database import get_session
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from models import Item, ItemStatus, User
from schemas import ItemCreate, ItemResponse, ItemUpdate
from sqlmodel import Session, select

router = APIRouter(prefix="/items", tags=["Items (Protected)"])


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: ItemCreate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Item:
    """
    Create a new item (requires authentication).

    Background tasks:
    - Send notification email
    - Log activity
    - Process item data
    """
    db_item = Item(
        **item_data.model_dump(),
        owner_id=current_user.id,
    )

    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    # Ensure ID is set after commit
    if db_item.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create item",
        )

    # Store ID in a variable to satisfy type checker
    item_id: int = db_item.id

    # Add background tasks (now item_id is guaranteed to be int)
    background_tasks.add_task(
        send_item_notification,
        owner_email=current_user.email,
        item_title=db_item.title,
        action="created",
    )
    assert current_user.id is not None, "User ID should not be None"
    background_tasks.add_task(
        log_item_activity,
        user_id=current_user.id,
        username=current_user.username,
        action="created",
        item_id=item_id,
        item_title=db_item.title,
    )
    background_tasks.add_task(
        process_item_data, item_id=item_id, item_title=db_item.title
    )

    return db_item


@router.get("/", response_model=list[ItemResponse])
def list_items(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: ItemStatus | None = Query(None, alias="status"),
    my_items_only: bool = Query(False, description="Show only my items"),
) -> list[Item]:
    """
    List items (requires authentication).

    Background tasks:
    - Log activity
    """
    statement = select(Item)

    if my_items_only:
        statement = statement.where(Item.owner_id == current_user.id)

    if status_filter:
        statement = statement.where(Item.status == status_filter)

    statement = statement.offset(skip).limit(limit)

    items = session.exec(statement).all()

    # Log activity in background
    assert current_user.id is not None, "User ID should not be None"
    background_tasks.add_task(
        log_item_activity,
        user_id=current_user.id,
        username=current_user.username,
        action=f"listed {len(items)} items",
    )

    return list(items)


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Item:
    """
    Get a specific item by ID (requires authentication).

    Background tasks:
    - Log view activity
    """
    item = session.get(Item, item_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )

    if item.owner_id != current_user.id and item.status != ItemStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this item",
        )

    # item.id is guaranteed to be int here (fetched from DB)
    assert item.id is not None, "Item ID should not be None"

    # Log view in background
    assert current_user.id is not None, "User ID should not be None"
    background_tasks.add_task(
        log_item_activity,
        user_id=current_user.id,
        username=current_user.username,
        action="viewed",
        item_id=item.id,
        item_title=item.title,
    )

    return item


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    item_data: ItemUpdate,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
) -> Item:
    """
    Update an item (requires authentication).

    Background tasks:
    - Send notification
    - Log activity
    - Regenerate statistics
    """
    db_item = session.get(Item, item_id)

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )

    if db_item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this item",
        )

    # Update fields
    update_data = item_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)

    db_item.updated_at = datetime.utcnow()

    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    # db_item.id is guaranteed to be int (fetched from DB)
    assert db_item.id is not None, "Item ID should not be None"

    # Add background tasks
    background_tasks.add_task(
        send_item_notification,
        owner_email=current_user.email,
        item_title=db_item.title,
        action="updated",
    )
    assert current_user.id is not None, "User ID should not be None"
    background_tasks.add_task(
        log_item_activity,
        user_id=current_user.id,
        username=current_user.username,
        action="updated",
        item_id=db_item.id,
        item_title=db_item.title,
    )
    background_tasks.add_task(generate_user_stats, user_id=current_user.id)

    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    """
    Delete an item (requires authentication).

    Background tasks:
    - Send notification
    - Log activity
    """
    db_item = session.get(Item, item_id)

    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found",
        )

    if db_item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this item",
        )

    item_title = db_item.title

    session.delete(db_item)
    session.commit()

    # Add background tasks (item_id from path parameter is int)
    background_tasks.add_task(
        send_item_notification,
        owner_email=current_user.email,
        item_title=item_title,
        action="deleted",
    )
    assert current_user.id is not None, "User ID should not be None"
    background_tasks.add_task(
        log_item_activity,
        user_id=current_user.id,
        username=current_user.username,
        action="deleted",
        item_id=item_id,  # Use path parameter (int) instead of db_item.id
        item_title=item_title,
    )
