"""
App Factory — FastAPI application entry point.

Creates the FastAPI app, mounts routers, registers global exception
handlers, and configures lifespan events (startup/shutdown).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from src.config import settings
from src.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)

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
        allow_origins=["*"],
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

    # Mount routers
    from src.auth.router import router as auth_router
    from src.courses.router import admin_router as courses_admin_router
    from src.courses.router import router as courses_router
    from src.courses.router import ui_router as courses_ui_router
    from src.lessons.router import router as lessons_router
    from src.lessons.router import ui_router as lessons_ui_router
    from src.progress.router import admin_router as progress_admin_router
    from src.progress.router import router as progress_router
    from src.quizzes.router import router as quizzes_router
    from src.submissions.router import admin_router as submissions_admin_router
    from src.submissions.router import router as submissions_router
    from src.users.router import admin_router as users_admin_router
    from src.users.router import router as users_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(users_admin_router, prefix="/api/v1")
    app.include_router(courses_router, prefix="/api/v1")
    app.include_router(courses_admin_router, prefix="/api/v1")
    app.include_router(courses_ui_router, prefix="/api/v1")
    app.include_router(lessons_router, prefix="/api/v1")
    app.include_router(lessons_ui_router, prefix="/api/v1")
    app.include_router(quizzes_router, prefix="/api/v1")
    app.include_router(submissions_router, prefix="/api/v1")
    app.include_router(submissions_admin_router, prefix="/api/v1")
    app.include_router(progress_router, prefix="/api/v1")
    app.include_router(progress_admin_router, prefix="/api/v1")

    # Health check
    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    # SQLAdmin UI — mounted at /admin
    # SessionMiddleware must be added AFTER routes to avoid double-wrapping CORS
    from sqladmin import Admin
    from starlette.middleware.sessions import SessionMiddleware

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
    from src.core.database import engine

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
