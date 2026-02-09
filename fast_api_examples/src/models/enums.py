"""Enum definitions for FastAPI examples."""

from enum import Enum


class ItemCategory(str, Enum):
    """Item category enum."""

    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    BOOKS = "books"
