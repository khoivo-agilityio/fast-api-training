"""Background task functions for simulated email notifications.

These are plain sync functions — FastAPI BackgroundTasks accepts both sync
and async callables. Keeping them sync keeps the implementation simple since
they only log and do no I/O.
"""

import structlog

logger = structlog.get_logger(__name__)


def simulate_task_assignment_email(
    task_id: int,
    task_title: str,
    assignee_id: int,
    project_id: int,
) -> None:
    """Simulate sending an email when a task is assigned to a user."""
    logger.info(
        "email_sent",
        email_type="task_assigned",
        task_id=task_id,
        task_title=task_title,
        assignee_id=assignee_id,
        project_id=project_id,
        message=(
            f"Simulated email: Task '{task_title}' (ID={task_id}) "
            f"assigned to user {assignee_id} in project {project_id}."
        ),
    )


def simulate_project_created_email(
    project_id: int,
    project_name: str,
    owner_id: int,
) -> None:
    """Simulate sending an email when a new project is created."""
    logger.info(
        "email_sent",
        email_type="project_created",
        project_id=project_id,
        project_name=project_name,
        owner_id=owner_id,
        message=(
            f"Simulated email: Project '{project_name}' (ID={project_id}) "
            f"created by user {owner_id}."
        ),
    )


def simulate_welcome_email(
    user_id: int,
    username: str,
    email: str,
) -> None:
    """Simulate sending a welcome email when a new user registers."""
    logger.info(
        "email_sent",
        email_type="welcome",
        user_id=user_id,
        username=username,
        email=email,
        message=(
            f"Simulated email: Welcome to the platform, {username}! "
            f"(ID={user_id}, email={email})"
        ),
    )
