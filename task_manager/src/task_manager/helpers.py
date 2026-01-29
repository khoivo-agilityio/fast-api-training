from pathlib import Path

import typer

from .enums import TaskStatus
from .models import Task
from .repositories.task_repo import TaskRepository
from .services import TaskService

# Default data file location
DEFAULT_DATA_FILE = Path.home() / ".task_manager" / "tasks.json"


# ============================================================================
# SERVICE HELPERS
# ============================================================================


def get_service(data_file: Path | None = None) -> TaskService:
    """
    Get TaskService instance with configured repository.

    Args:
        data_file: Optional custom data file path

    Returns:
        Configured TaskService instance
    """
    file_path = data_file or DEFAULT_DATA_FILE
    repository = TaskRepository(file_path)
    return TaskService(repository)


# ============================================================================
# FORMATTING HELPERS
# ============================================================================


def format_status(status: TaskStatus | str) -> str:
    """
    Format status for better UX.

    Args:
        status: TaskStatus enum or string value

    Returns:
        Formatted status string
    """
    if isinstance(status, TaskStatus):
        return status.value.upper()

    return TaskStatus.from_string(status).format()


# ============================================================================
# DISPLAY HELPERS
# ============================================================================


def echo(message: str = "") -> None:
    """
    Print a message to stdout.

    Args:
        message: Message to print (empty for blank line)
    """
    typer.echo(message)


def echo_success(message: str) -> None:
    """
    Print a success message in green with checkmark.

    Args:
        message: Success message to display
    """
    typer.secho(f"{message}", fg=typer.colors.GREEN, bold=True)


def echo_error(message: str) -> None:
    """
    Print an error message in red.

    Args:
        message: Error message to display
    """
    typer.secho(f"✗ {message}", fg=typer.colors.RED, bold=True)


def echo_warning(message: str) -> None:
    """
    Print a warning message in yellow.

    Args:
        message: Warning message to display
    """
    typer.secho(message, fg=typer.colors.YELLOW)


def echo_info(message: str, bold: bool = False) -> None:
    """
    Print an info message in cyan.

    Args:
        message: Info message to display
        bold: Whether to make the text bold
    """
    typer.secho(message, fg=typer.colors.CYAN, bold=bold)


def echo_header(message: str) -> None:
    """
    Print a section header in cyan and bold.

    Args:
        message: Header text to display
    """
    typer.secho(message, fg=typer.colors.CYAN, bold=True)


# ============================================================================
# TASK DISPLAY HELPERS
# ============================================================================


def print_task_details(task: Task, show_timestamps: bool = False) -> None:
    """
    Print task details in a consistent format.

    Args:
        task: Task to display
        show_timestamps: Whether to show created/updated timestamps
    """
    echo(f"ID: {task.id}")
    echo(f"Title: {task.title}")
    echo(f"Status: {format_status(task.status)}")

    if task.description:
        echo(f"Description: {task.description}")

    if show_timestamps:
        echo(f"Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        echo(f"Updated: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")


def print_task_created(task: Task) -> None:
    """
    Print task creation success message with details.

    Args:
        task: Newly created task
    """
    echo()
    echo_success("Task created successfully!")
    print_task_details(task)
    echo()


def print_task_updated(task: Task, action: str = "updated") -> None:
    """
    Print task update success message with details.

    Args:
        task: Updated task
        action: Action description (e.g., "updated", "marked as done")
    """
    echo()
    echo_success(f"Task {action} successfully!")
    print_task_details(task, show_timestamps=True)
    echo()


def print_task_deleted(task_id: int, title: str) -> None:
    """
    Print task deletion success message.

    Args:
        task_id: ID of deleted task
        title: Title of deleted task
    """
    echo()
    echo_success(f"Task #{task_id} deleted successfully!")
    echo(f"Title: {title}")
    echo()


def print_task_info(task: Task) -> None:
    """
    Print detailed task information with header.

    Args:
        task: Task to display
    """
    echo()
    echo_header(f"Task #{task.id}")
    print_task_details(task, show_timestamps=True)
    echo()


def print_tasks_table(tasks: list[Task]) -> None:
    """
    Print tasks in a simple ASCII table format.

    Args:
        tasks: List of tasks to display
    """
    echo()
    echo_header(f"Tasks ({len(tasks)} total)")
    echo("-" * 80)
    echo(f"{'ID':<6} {'Title':<40} {'Status':<20} {'Created':<14}")
    echo("-" * 80)

    for task in tasks:
        created_str = task.created_at.strftime("%Y-%m-%d %H:%M")
        title_display = task.title[:37] + "..." if len(task.title) > 40 else task.title
        echo(
            f"{task.id:<6} {title_display:<40} "
            f"{format_status(task.status):<20} {created_str:<14}"
        )

    echo("-" * 80)
    echo()


def print_no_tasks(status_filter: TaskStatus | None = None) -> None:
    """
    Print message when no tasks are found.

    Args:
        status_filter: Optional status filter that was applied
    """
    echo()
    if status_filter:
        echo_warning(f"No tasks found with status: {format_status(status_filter)}")
    else:
        echo_warning("No tasks yet. Add one with:")
        echo('  task add "Your first task"')
    echo()


def print_summary(stats: dict) -> None:
    """
    Print task summary statistics.

    Args:
        stats: Dictionary containing task statistics
    """
    echo()
    echo_header("Task Summary")
    echo()
    echo(f"Total Tasks: {stats['total']}")
    echo(f"- Backlog: {stats['backlog']}")
    echo(f"- To Do: {stats['todo']}")
    echo(f"- In Progress: {stats['in_progress']}")
    echo(f"- Testing: {stats['testing']}")
    echo(f"- Done: {stats['done']}")
    echo()
    typer.secho(
        f"Completion: {stats['completion_percentage']:.1f}%",
        fg=typer.colors.GREEN,
        bold=True,
    )
    echo()


# ============================================================================
# ERROR HANDLING
# ============================================================================


def handle_error(error: Exception) -> None:
    """
    Handle and display errors gracefully.

    Args:
        error: Exception to handle

    Raises:
        typer.Exit: Always exits with code 1
    """
    echo_error(f"Error: {str(error)}")
    raise typer.Exit(code=1)
