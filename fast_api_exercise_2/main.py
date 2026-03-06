"""Main FastAPI application."""

from database import create_db_and_tables
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, items, public_items, websocket_router
from tags import tags_metadata

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

app = FastAPI(
    title="FastAPI Exercise 2 - Advanced",
    description="""
    🚀 **FastAPI Advanced Features Demo**
    
    This application demonstrates advanced FastAPI features:
    
    ## Features
    
    * 🔐 **JWT Authentication** - Secure token-based auth
    * 📦 **CRUD Operations** - Complete item management
    * 🔌 **WebSocket** - Real-time communication
    * 🏷️ **Enum Tags** - Type-safe API organization
    * 📝 **Background Tasks** - Async operations
    * 🗄️ **SQLModel** - Modern database ORM
    * 📊 **Automatic Docs** - Interactive API documentation
    
    ## Authentication
    
    1. Register a user: `POST /register`
    2. Login to get token: `POST /token`
    3. Use token in requests: `Authorization: Bearer <token>`
    
    ## Quick Start
    
    ```bash
    # Register
    curl -X POST "http://localhost:8000/register" \\
      -H "Content-Type: application/json" \\
      -d '{"username":"john","email":"john@example.com","password":"secret123"}'
    
    # Login
    curl -X POST "http://localhost:8000/token" \\
      -d "username=john&password=secret123"
    
    # Use token
    TOKEN="your_token_here"
    curl -X GET "http://localhost:8000/items/" \\
      -H "Authorization: Bearer $TOKEN"
    ```
    
    ## WebSocket
    
    Connect to WebSocket for real-time updates:
    ```
    ws://localhost:8000/ws/{token}
    ```
    
    Test page: [/ws-test](/ws-test)
    """,
    version="2.0.0",
    terms_of_service="https://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "https://example.com/support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=tags_metadata,  # 🏷️ Add tags metadata
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS middleware for WebSocket
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# LIFECYCLE EVENTS
# ============================================================================


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()
    print("✅ Database initialized")


@app.on_event("shutdown")
def on_shutdown():
    """Cleanup on shutdown."""
    print("👋 Application shutting down")


# ============================================================================
# ROUTERS
# ============================================================================

# Include routers
app.include_router(auth.router)
app.include_router(public_items.router)
app.include_router(items.router)
app.include_router(websocket_router.router)

# ============================================================================
# ROOT ENDPOINTS
# ============================================================================


@app.get(
    "/",
    tags=["Root"],
    summary="Root endpoint",
    description="Welcome message with links to documentation",
    response_description="Welcome message and API info",
)
def read_root():
    """
    Root endpoint with API information.

    Returns links to:
    - Interactive documentation (Swagger UI)
    - WebSocket test page
    - API version and status
    """
    return {
        "message": "Welcome to FastAPI Exercise 2 with WebSocket!",
        "version": "2.0.0",
        "status": "operational",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
        },
        "websocket": {
            "test_page": "/ws-test",
            "endpoint": "/ws/{token}",
        },
        "quick_start": {
            "1_register": "POST /register",
            "2_login": "POST /token",
            "3_create_item": "POST /items/ (with Authorization header)",
        },
    }


@app.get(
    "/health",
    tags=["Health & Monitoring"],
    summary="Health check",
    description="Check if the API is running and healthy",
    response_description="Health status",
)
def health_check():
    """
    Health check endpoint.

    Returns:
    - Status: API operational status
    - Version: Current API version
    - Database: Database connection status
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": "connected",
    }
