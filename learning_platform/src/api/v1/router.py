"""
API v1 Router — aggregates all v1 domain routers.

Mount this in main.py with: app.include_router(v1_router, prefix="/api/v1")
"""

from fastapi import APIRouter

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

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(users_admin_router)
v1_router.include_router(courses_router)
v1_router.include_router(courses_admin_router)
v1_router.include_router(courses_ui_router)
v1_router.include_router(lessons_router)
v1_router.include_router(lessons_ui_router)
v1_router.include_router(quizzes_router)
v1_router.include_router(submissions_router)
v1_router.include_router(submissions_admin_router)
v1_router.include_router(progress_router)
v1_router.include_router(progress_admin_router)
