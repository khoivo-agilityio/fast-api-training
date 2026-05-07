"""Quiz module exceptions."""

from src.exceptions import ConflictError, NotFoundError


class QuizNotFound(NotFoundError):
    def __init__(self, identifier: object = None):
        detail = f"Quiz not found: {identifier}" if identifier else "Quiz not found"
        super().__init__(detail=detail, error_code="QUIZ_NOT_FOUND")


class QuestionNotFound(NotFoundError):
    def __init__(self, identifier: object = None):
        detail = (
            f"Question not found: {identifier}" if identifier else "Question not found"
        )
        super().__init__(detail=detail, error_code="QUESTION_NOT_FOUND")


class QuizAlreadyExists(ConflictError):
    def __init__(self):
        super().__init__(
            detail="This lesson already has a quiz",
            error_code="QUIZ_ALREADY_EXISTS",
        )
