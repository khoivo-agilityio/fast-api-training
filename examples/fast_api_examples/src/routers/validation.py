"""Query and Path parameter validation examples.

Based on FastAPI documentation:
- https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
- https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/
"""

from typing import Annotated

from fastapi import APIRouter, Path, Query

router = APIRouter(prefix="/validation", tags=["Validation"])


# ============================================================================
# QUERY PARAMETERS - STRING VALIDATIONS
# ============================================================================


@router.get("/items/")
def read_items(
    q: Annotated[str | None, Query(max_length=50)] = None,
) -> dict:
    """
    Query parameter with max length validation.

    - q: Optional query string, max 50 characters
    """
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@router.get("/items/min-length/")
def read_items_min_length(
    q: Annotated[str | None, Query(min_length=3, max_length=50)] = None,
) -> dict:
    """
    Query parameter with min and max length validation.

    - q: Optional query string, 3-50 characters
    """
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@router.get("/items/regex/")
def read_items_regex(
    q: Annotated[
        str | None,
        Query(
            min_length=3,
            max_length=50,
            pattern="^[a-zA-Z0-9_-]+$",
        ),
    ] = None,
) -> dict:
    """
    Query parameter with regex pattern validation.

    - q: Optional, alphanumeric with underscores and hyphens only
    """
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@router.get("/items/multiple/")
def read_items_multiple(
    q: Annotated[list[str] | None, Query()] = None,
) -> dict:
    """
    Multiple query parameters with the same name.

    Example: /items/multiple/?q=foo&q=bar
    """
    query_items = {"q": q}
    return query_items


@router.get("/items/default-list/")
def read_items_default_list(
    q: Annotated[list[str], Query()] = ["foo", "bar"],
) -> dict:
    """
    Query parameter with default list value.
    """
    query_items = {"q": q}
    return query_items


@router.get("/items/metadata/")
def read_items_metadata(
    q: Annotated[
        str | None,
        Query(
            title="Query string",
            description="Query string for the items to search in the database",
            min_length=3,
            max_length=50,
            alias="item-query",
            deprecated=False,
        ),
    ] = None,
) -> dict:
    """
    Query parameter with metadata for documentation.

    - title: Shows in OpenAPI docs
    - description: Detailed description
    - alias: Use 'item-query' instead of 'q' in URL
    - deprecated: Mark parameter as deprecated
    """
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    return results


@router.get("/items/required/")
def read_items_required(
    q: Annotated[str, Query(min_length=3)],
) -> dict:
    """
    Required query parameter (no default value).

    - q: Required query string, minimum 3 characters
    """
    results = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    results.update({"q": q})
    return results


# ============================================================================
# PATH PARAMETERS - NUMERIC VALIDATIONS
# ============================================================================


@router.get("/items/{item_id}")
def read_item_path(
    item_id: Annotated[int, Path(title="The ID of the item to get")],
    q: Annotated[str | None, Query(alias="item-query")] = None,
) -> dict:
    """
    Path parameter with title metadata.
    """
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results


@router.get("/items/gt/{item_id}")
def read_item_gt(
    item_id: Annotated[int, Path(title="The ID of the item to get", gt=0)],
    q: str | None = None,
) -> dict:
    """
    Path parameter with greater than validation.

    - item_id: Must be greater than 0
    """
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results


@router.get("/items/ge/{item_id}")
def read_item_ge(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=1)],
) -> dict:
    """
    Path parameter with greater than or equal validation.

    - item_id: Must be >= 1
    """
    results = {"item_id": item_id}
    return results


@router.get("/items/range/{item_id}")
def read_item_range(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=1, le=1000)],
) -> dict:
    """
    Path parameter with range validation.

    - item_id: Must be between 1 and 1000 (inclusive)
    """
    results = {"item_id": item_id}
    return results


@router.get("/items/float/{item_id}")
def read_item_float(
    *,
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=0, le=1000)],
    q: str,
    size: Annotated[float, Query(gt=0, lt=10.5)],
) -> dict:
    """
    Mixed path and query parameters with numeric validations.

    - item_id: Integer, 0-1000 (inclusive)
    - q: Required query string
    - size: Float, must be > 0 and < 10.5

    Note: Using * forces all parameters to be keyword-only
    """
    results = {"item_id": item_id, "q": q, "size": size}
    return results


# ============================================================================
# COMBINED VALIDATIONS
# ============================================================================


@router.get("/products/{product_id}")
def read_product(
    product_id: Annotated[
        int,
        Path(
            title="Product ID",
            description="The unique identifier for the product",
            ge=1,
            le=999999,
        ),
    ],
    name: Annotated[
        str | None,
        Query(
            title="Product name filter",
            description="Filter products by name",
            min_length=1,
            max_length=100,
            pattern="^[a-zA-Z0-9 -]+$",
        ),
    ] = None,
    category: Annotated[
        list[str] | None,
        Query(
            title="Product categories",
            description="Filter by one or more categories",
            max_length=50,
        ),
    ] = None,
    min_price: Annotated[
        float | None,
        Query(
            title="Minimum price",
            description="Filter products with price >= this value",
            ge=0,
            le=1000000,
        ),
    ] = None,
    max_price: Annotated[
        float | None,
        Query(
            title="Maximum price",
            description="Filter products with price <= this value",
            ge=0,
            le=1000000,
        ),
    ] = None,
    in_stock: Annotated[
        bool | None,
        Query(
            title="In stock filter",
            description="Filter by stock availability",
        ),
    ] = None,
) -> dict:
    """
    Complex example with multiple validated parameters.

    Demonstrates:
    - Path parameter with numeric range validation
    - String query parameter with pattern validation
    - List query parameter for multiple values
    - Float query parameters with range validation
    - Boolean query parameter
    """
    result = {
        "product_id": product_id,
        "filters": {
            "name": name,
            "categories": category,
            "price_range": {
                "min": min_price,
                "max": max_price,
            },
            "in_stock": in_stock,
        },
    }
    return result
