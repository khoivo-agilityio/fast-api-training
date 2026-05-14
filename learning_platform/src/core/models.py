"""
ORM Model Re-exports — for Alembic autogenerate.

Import all ORM models here so that Alembic's `target_metadata = Base.metadata`
sees every table. Without this, `alembic revision --autogenerate` creates empty
migrations (see gotchas.md #3).

Add new model imports here whenever a new module's models.py is created.
"""

from src.courses.models import Course, Enrollment  # noqa: F401
from src.lessons.models import Lesson  # noqa: F401
from src.progress.models import Progress  # noqa: F401
from src.quizzes.models import Question, Quiz  # noqa: F401
from src.submissions.models import Answer, Submission  # noqa: F401
from src.users.models import User  # noqa: F401
