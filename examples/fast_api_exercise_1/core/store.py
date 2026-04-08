"""In-memory data store for items."""

from models.item import Item, ItemStatus


class ItemStore:
    """In-memory storage for items."""

    def __init__(self):
        """Initialize the store with empty data."""
        self._items: dict[int, Item] = {}
        self._next_id: int = 1

    def create(
        self,
        name: str,
        price: float,
        status: ItemStatus,
        description: str | None = None,
    ) -> Item:
        """Create a new item."""
        item = Item(
            id=self._next_id,
            name=name,
            description=description,
            price=price,
            status=status,
        )
        self._items[item.id] = item
        self._next_id += 1
        return item

    def get_all(
        self,
        status: ItemStatus | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> list[Item]:
        """Get all items with optional filtering."""
        items = list(self._items.values())

        # Apply filters
        if status is not None:
            items = [item for item in items if item.status == status]
        if min_price is not None:
            items = [item for item in items if item.price >= min_price]
        if max_price is not None:
            items = [item for item in items if item.price <= max_price]

        return items

    def get_by_id(self, item_id: int) -> Item | None:
        """Get an item by ID."""
        return self._items.get(item_id)

    def update(
        self,
        item_id: int,
        name: str | None = None,
        description: str | None = None,
        price: float | None = None,
        status: ItemStatus | None = None,
    ) -> Item | None:
        """Update an existing item."""
        item = self._items.get(item_id)
        if item is None:
            return None

        item.update(name=name, description=description, price=price, status=status)
        return item

    def delete(self, item_id: int) -> bool:
        """Delete an item by ID."""
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False


# Global store instance
item_store = ItemStore()
