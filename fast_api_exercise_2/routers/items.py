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
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from models import Item, User
from schemas import ItemCreate, ItemResponse, ItemUpdate
from sqlmodel import Session
from websocket_manager import manager  # Import WebSocket manager

router = APIRouter(prefix="/items", tags=["Items (Protected)"])


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(  # Changed to async
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

    WebSocket:
    - Notify all connected users about new item
    """
    db_item = Item(
        **item_data.model_dump(),
        owner_id=current_user.id,
    )

    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    if db_item.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create item",
        )

    item_id: int = db_item.id

    # Background tasks
    background_tasks.add_task(
        send_item_notification,
        owner_email=current_user.email,
        item_title=db_item.title,
        action="created",
    )
    if current_user.id is not None:
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

    # 🔌 WebSocket: Notify all connected users
    await manager.notify_item_created(
        item_id=item_id,
        item_title=db_item.title,
        owner_username=current_user.username,
    )

    return db_item


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(  # Changed to async
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

    WebSocket:
    - Notify all connected users about update
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

    # Track changes
    update_data = item_data.model_dump(exclude_unset=True)
    changes = {}

    for key, value in update_data.items():
        old_value = getattr(db_item, key)
        if old_value != value:
            changes[key] = {"old": old_value, "new": value}
        setattr(db_item, key, value)

    db_item.updated_at = datetime.utcnow()

    session.add(db_item)
    session.commit()
    session.refresh(db_item)

    assert db_item.id is not None, "Item ID should not be None"

    # Background tasks
    background_tasks.add_task(
        send_item_notification,
        owner_email=current_user.email,
        item_title=db_item.title,
        action="updated",
    )
    if current_user.id is not None:
        background_tasks.add_task(
            log_item_activity,
            user_id=current_user.id,
            username=current_user.username,
            action="updated",
            item_id=db_item.id,
            item_title=db_item.title,
        )
        background_tasks.add_task(generate_user_stats, user_id=current_user.id)

    # 🔌 WebSocket: Notify all connected users
    await manager.notify_item_updated(
        item_id=db_item.id,
        item_title=db_item.title,
        owner_username=current_user.username,
        changes=changes,
    )

    return db_item
