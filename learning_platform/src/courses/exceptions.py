"""Course module exceptions."""

from src.core.exceptions import AuthorizationError, ConflictError, NotFoundError


class CourseNotFound(NotFoundError):
    """Raised when a course is not found by ID."""

    def __init__(self, course_id: object = None):
        detail = f"Course not found: {course_id}" if course_id else "Course not found"
        super().__init__(detail=detail, error_code="COURSE_NOT_FOUND")


class AlreadyEnrolled(ConflictError):
    """Raised when a student tries to enroll in a course they're already in."""

    def __init__(self):
        super().__init__(
            detail="Already enrolled in this course",
            error_code="ALREADY_ENROLLED",
        )


class NotCourseOwner(AuthorizationError):
    """Raised when an instructor tries to modify a course they don't own."""

    def __init__(self):
        super().__init__(
            detail="You are not the owner of this course",
            error_code="NOT_COURSE_OWNER",
        )


class NotEnrolled(AuthorizationError):
    """Raised when a student tries to access content of a course they're not enrolled in."""

    def __init__(self):
        super().__init__(
            detail="You are not enrolled in this course",
            error_code="NOT_ENROLLED",
        )
