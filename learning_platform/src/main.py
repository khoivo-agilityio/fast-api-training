"""
App Factory — FastAPI application entry point.

Creates the FastAPI app, mounts routers, registers global exception
handlers, and configures lifespan events (startup/shutdown).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.config import settings
from sqladmin import Admin
from src.admin_view import (
    AdminAuthBackend,
    AnswerAdmin,
    CourseAdmin,
    EnrollmentAdmin,
    LessonAdmin,
    ProgressAdmin,
    QuestionAdmin,
    QuizAdmin,
    SubmissionAdmin,
    UserAdmin,
)
from src.api.v1.router import v1_router
from src.api.v2.router import v2_router
from src.core.database import engine
from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)
from src.core.logging import configure_logging
from starlette.middleware.sessions import SessionMiddleware

# Status code mapping — walks MRO to find first matching parent (gotchas.md #2)
_STATUS_MAP: dict[type, int] = {
    NotFoundError: 404,
    AuthenticationError: 401,
    AuthorizationError: 403,
    ConflictError: 409,
    ValidationError: 422,
    DomainError: 400,
}


def _resolve_status(exc: DomainError) -> int:
    """Walk the MRO to find the first matching status code.

    This avoids the bug where subclass exceptions (e.g. InvalidCredentials)
    miss their parent's mapped status code (see gotchas.md #2).
    """
    for cls in type(exc).__mro__:
        if cls in _STATUS_MAP:
            return _STATUS_MAP[cls]
    return 400


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    configure_logging(settings.ENABLE_DEBUG)
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description=(
            "Backend REST API for an **AI-Enhanced Learning Platform**.\n\n"
            "### Features\n"
            "- JWT authentication with refresh-token rotation\n"
            "- Role-based access control (Admin / Instructor / Student)\n"
            "- Course & Lesson management (CRUD)\n"
            "- Quiz auto-grading (single / multiple choice)\n"
            "- Course progress tracking\n"
            "- SQLAdmin UI at `/admin`\n\n"
            "### Auth\n"
            "Use `POST /api/v1/auth/login` to obtain tokens. "
            "Pass the `access_token` as `Bearer <token>` in the `Authorization` header."
        ),
        openapi_tags=[
            {
                "name": "auth",
                "description": "Register, login, refresh tokens, and logout.",
            },
            {
                "name": "users",
                "description": "View and update your own profile.",
            },
            {
                "name": "courses",
                "description": (
                    "Create, list, update, publish, and delete courses. "
                    "Students can enroll in published courses."
                ),
            },
            {
                "name": "lessons",
                "description": (
                    "Manage lessons within a course. "
                    "Viewing a lesson (with no quiz) automatically marks it complete."
                ),
            },
            {
                "name": "quizzes",
                "description": (
                    "Create and manage quizzes and their questions. "
                    "Students see questions without correct answers."
                ),
            },
            {
                "name": "submissions",
                "description": (
                    "Submit quiz answers (one attempt per quiz). "
                    "Scores are computed automatically."
                ),
            },
            {
                "name": "progress",
                "description": "View course-level and lesson-level progress for enrolled courses.",
            },
            {
                "name": "admin",
                "description": "Admin-only REST endpoints. Mirrors the SQLAdmin UI at `/admin`.",
            },
            {
                "name": "system",
                "description": "Health check and operational endpoints.",
            },
        ],
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler for DomainError hierarchy
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=_resolve_status(exc),
            content={"detail": exc.detail, "error_code": exc.error_code},
        )

    # Rate limiter — slowapi
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Mount versioned API routers
    app.include_router(v1_router)
    app.include_router(v2_router)

    # Health check
    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    # SQLAdmin UI — mounted at /admin
    # SessionMiddleware must be added AFTER routes to avoid double-wrapping CORS
    # Trust X-Forwarded-Proto/For headers from Railway's reverse proxy
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
    # https_only=False because TLS is terminated at the Railway proxy, not the app
    app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET, https_only=False)

    admin = Admin(
        app,
        engine,
        authentication_backend=AdminAuthBackend(secret_key=settings.JWT_SECRET),
        templates_dir="templates",
    )
    admin.add_view(UserAdmin)
    admin.add_view(CourseAdmin)
    admin.add_view(EnrollmentAdmin)
    admin.add_view(LessonAdmin)
    admin.add_view(QuizAdmin)
    admin.add_view(QuestionAdmin)
    admin.add_view(SubmissionAdmin)
    admin.add_view(AnswerAdmin)
    admin.add_view(ProgressAdmin)

    return app


app = create_app()
