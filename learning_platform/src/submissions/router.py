"""
Submission Router — /api/v1/quizzes/{quiz_id}/submit + /api/v1/quizzes/{quiz_id}/submission.

Thin router: no try/except, no DB queries, no business logic.
Parse params → call service → return schema.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import get_current_user, require_roles
from src.submissions.dependencies import get_submission_service
from src.submissions.schemas import SubmissionDetailResponse, SubmitQuizRequest
from src.submissions.service import SubmissionService
from src.users.models import User

router = APIRouter(tags=["submissions"])


@router.post(
    "/quizzes/{quiz_id}/submit",
    response_model=SubmissionDetailResponse,
    status_code=201,
)
async def submit_quiz(
    quiz_id: UUID,
    data: SubmitQuizRequest,
    current_user: User = Depends(require_roles("student")),
    service: SubmissionService = Depends(get_submission_service),
) -> SubmissionDetailResponse:
    """Submit quiz answers. Auto-grades and returns results (Student only, enrolled)."""
    return await service.submit(quiz_id, current_user.id, data)


@router.get(
    "/quizzes/{quiz_id}/submission",
    response_model=SubmissionDetailResponse,
)
async def get_submission(
    quiz_id: UUID,
    current_user: User = Depends(get_current_user),
    service: SubmissionService = Depends(get_submission_service),
) -> SubmissionDetailResponse:
    """Get own submission for a quiz with answer results."""
    return await service.get_submission_with_answers(quiz_id, current_user.id)


# ---------------------------------------------------------------------------
# Admin-only endpoints — /api/v1/admin/submissions/*
# ---------------------------------------------------------------------------

admin_router = APIRouter(prefix="/admin/submissions", tags=["admin"])


@admin_router.get("", response_model=list[dict])
async def admin_list_submissions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_roles("admin")),
    service: SubmissionService = Depends(get_submission_service),
) -> list[dict]:
    """List all quiz submissions (admin only)."""
    submissions = await service.list_all(limit=limit, offset=offset)
    return [
        {
            "id": str(s.id),
            "user_id": str(s.user_id),
            "quiz_id": str(s.quiz_id),
            "score": s.score,
            "submitted_at": s.submitted_at.isoformat(),
        }
        for s in submissions
    ]


@admin_router.delete("/{submission_id}", status_code=204)
async def admin_delete_submission(
    submission_id: UUID,
    _: None = Depends(require_roles("admin")),
    service: SubmissionService = Depends(get_submission_service),
) -> None:
    """Delete a submission (admin only)."""
    await service.delete(submission_id)
