# FastAPI Exercise 1: In-Memory CRUD API

A complete FastAPI application demonstrating CRUD operations with in-memory storage, strong Pydantic validation, and automatically generated API documentation.

## 🎯 Learning Objectives

- ✅ Understand FastAPI request/response flow
- ✅ Master Pydantic data validation
- ✅ Design clean CRUD APIs with proper HTTP status codes
- ✅ Utilize auto-generated API documentation (Swagger UI & ReDoc)
- ✅ Separate concerns (models, schemas, routes, storage)

## 📋 Features

- **CRUD Operations**: Create, Read, Update, Delete items
- **In-Memory Storage**: Data stored in Python dict (resets on restart)
- **Data Validation**: Strong type checking and validation with Pydantic
- **Filtering**: Query items by status, price range
- **Auto-Generated Docs**: Interactive Swagger UI and ReDoc
- **Proper Status Codes**: 200, 201, 204, 404, 422
- **Clean Architecture**: Separation of models, schemas, routes, and storage

## 🚀 Quick Start

### Installation

```bash
# Using uv (recommended)
cd fast_api_exercise_1
uv pip install fastapi "uvicorn[standard]" pydantic

# Or using pip
pip install fastapi "uvicorn[standard]" pydantic
```

### Run the Application

```bash
# Using uv
uv run uvicorn main:app --reload

# Or using uvicorn directly
uvicorn main:app --reload
```

The API will be available at: **http://127.0.0.1:8000**

### Interactive Documentation

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📂 Project Structure

```
fast_api_exercise_1/
├── main.py                      # FastAPI application entry point
├── apis/
│   ├── __init__.py
│   └── items.py                 # Items CRUD endpoints
├── core/
│   ├── __init__.py
│   └── store.py                 # In-memory storage implementation
├── models/
│   ├── __init__.py
│   └── item.py                  # Item model and ItemStatus enum
├── schemas/
│   ├── __init__.py
│   └── item.py                  # Pydantic schemas (validation)
├── pyproject.toml               # Project configuration
├── README.md                    # This file
└── requirement.md               # Detailed requirements
```

## 📊 Data Model

### Item Entity

| Field       | Type       | Required | Description           | Validation         |
| ----------- | ---------- | -------- | --------------------- | ------------------ |
| id          | int        | Yes      | Unique identifier     | Auto-generated     |
| name        | str        | Yes      | Item name             | 1-100 characters   |
| description | str        | No       | Item description      | Max 500 characters |
| price       | float      | Yes      | Item price            | Must be > 0        |
| status      | ItemStatus | Yes      | Business state        | Enum value         |
| created_at  | datetime   | Yes      | Creation timestamp    | Auto-generated     |
| updated_at  | datetime   | Yes      | Last update timestamp | Auto-generated     |

### Item Status Enum

- `active` - Item is active and available
- `inactive` - Item is temporarily inactive
- `archived` - Item is archived and not available

## 🔌 API Endpoints

### Base URL

```
/api/v1/items
```

### 1. Create Item

```bash
POST /api/v1/items
Content-Type: application/json

{
  "name": "Laptop",
  "description": "High-performance laptop",
  "price": 999.99,
  "status": "active"
}
```

**Response: 201 Created**

```json
{
  "id": 1,
  "name": "Laptop",
  "description": "High-performance laptop",
  "price": 999.99,
  "status": "active",
  "created_at": "2026-02-11T17:00:00.000000",
  "updated_at": "2026-02-11T17:00:00.000000"
}
```

### 2. Get All Items

```bash
GET /api/v1/items
GET /api/v1/items?status=active
GET /api/v1/items?min_price=100&max_price=2000
GET /api/v1/items?status=active&min_price=500
```

**Response: 200 OK**

```json
[
  {
    "id": 1,
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": 999.99,
    "status": "active",
    "created_at": "2026-02-11T17:00:00.000000",
    "updated_at": "2026-02-11T17:00:00.000000"
  }
]
```

### 3. Get Item by ID

```bash
GET /api/v1/items/1
```

**Response: 200 OK** (or 404 Not Found)

### 4. Update Item

```bash
PUT /api/v1/items/1
Content-Type: application/json

{
  "name": "Updated Laptop",
  "price": 899.99,
  "status": "inactive"
}
```

**Response: 200 OK** (or 404 Not Found)

### 5. Delete Item

```bash
DELETE /api/v1/items/1
```

**Response: 204 No Content** (or 404 Not Found)

## 🧪 Testing Examples

### Using curl

```bash
# Create an item
curl -X POST "http://localhost:8000/api/v1/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "High-performance laptop",
    "price": 999.99,
    "status": "active"
  }'

# Get all items
curl "http://localhost:8000/api/v1/items"

# Filter by status
curl "http://localhost:8000/api/v1/items?status=active"

# Filter by price range
curl "http://localhost:8000/api/v1/items?min_price=500&max_price=1500"

# Get item by ID
curl "http://localhost:8000/api/v1/items/1"

# Update item
curl -X PUT "http://localhost:8000/api/v1/items/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Laptop",
    "price": 899.99
  }'

# Delete item
curl -X DELETE "http://localhost:8000/api/v1/items/1"
```

### Using Python requests

```python
import requests

base_url = "http://localhost:8000/api/v1/items"

# Create item
response = requests.post(
    base_url,
    json={
        "name": "Laptop",
        "description": "High-performance laptop",
        "price": 999.99,
        "status": "active"
    }
)
print(f"Created: {response.json()}")

# Get all items
response = requests.get(base_url)
print(f"All items: {response.json()}")

# Filter by status
response = requests.get(base_url, params={"status": "active"})
print(f"Active items: {response.json()}")

# Get item by ID
response = requests.get(f"{base_url}/1")
print(f"Item 1: {response.json()}")

# Update item
response = requests.put(
    f"{base_url}/1",
    json={
        "name": "Updated Laptop",
        "price": 899.99
    }
)
print(f"Updated: {response.json()}")

# Delete item
response = requests.delete(f"{base_url}/1")
print(f"Deleted: {response.status_code}")
```

## 🔍 Validation Examples

### Valid Request

```json
{
  "name": "Valid Item",
  "description": "This is valid",
  "price": 99.99,
  "status": "active"
}
```

### Invalid Requests (422 Validation Error)

```json
// Empty name
{
  "name": "",
  "price": 99.99,
  "status": "active"
}

// Negative price
{
  "name": "Invalid Item",
  "price": -10,
  "status": "active"
}

// Invalid status
{
  "name": "Invalid Item",
  "price": 99.99,
  "status": "invalid_status"
}

// Name too long (> 100 characters)
{
  "name": "A".repeat(101),
  "price": 99.99,
  "status": "active"
}
```

## 📚 Key Concepts Demonstrated

### 1. Pydantic Schemas

- **ItemBase**: Shared fields between create/response
- **ItemCreate**: Input validation for creating items
- **ItemUpdate**: All fields optional for partial updates
- **ItemResponse**: Includes id and timestamps

### 2. HTTP Status Codes

- `200 OK`: Successful GET/PUT
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error

### 3. In-Memory Storage

- Dictionary-based storage: `dict[int, Item]`
- Auto-incrementing ID counter
- Filtering capabilities
- Encapsulated in `ItemStore` class

### 4. Clean Architecture

```
main.py (FastAPI app)
    ↓
apis/items.py (Endpoints)
    ↓
schemas/item.py (Validation)
    ↓
core/store.py (Storage)
    ↓
models/item.py (Domain model)
```

## 🚀 Extension Ideas

- [ ] Add pagination (skip, limit parameters)
- [ ] Add sorting (order_by parameter)
- [ ] Implement soft delete (deleted_at field)
- [ ] Add authentication/authorization
- [ ] Replace in-memory store with SQLAlchemy + database
- [ ] Add search functionality
- [ ] Add bulk operations
- [ ] Add request/response logging
- [ ] Add rate limiting
- [ ] Add OpenAPI custom documentation

## 📝 Notes

- **Data is not persisted**: All data is lost when the application restarts
- **No concurrency protection**: Not suitable for production without proper database
- **Auto-generated IDs**: IDs increment from 1
- **Timestamps in ISO format**: All datetime fields use ISO 8601 format
- **Validation is automatic**: FastAPI handles validation before reaching endpoints

## 📖 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [REST API Best Practices](https://restfulapi.net/)

---

**Created**: February 11, 2026  
**FastAPI Version**: 0.128+  
**Python Version**: 3.11+
