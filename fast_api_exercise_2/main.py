"""Main FastAPI application."""

from database import create_db_and_tables
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, items, public_items, websocket_router

app = FastAPI(
    title="FastAPI Exercise 2",
    description="Authenticated CRUD API with WebSocket support",
    version="2.0.0",
)

# CORS middleware for WebSocket
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create database tables on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# Include routers
app.include_router(auth.router)
app.include_router(public_items.router)
app.include_router(items.router)
app.include_router(websocket_router.router)  # Add WebSocket router


@app.get("/")
def read_root():
    return {
        "message": "Welcome to FastAPI Exercise 2 with WebSocket!",
        "docs": "/docs",
        "websocket_test": "/ws-test",
    }
