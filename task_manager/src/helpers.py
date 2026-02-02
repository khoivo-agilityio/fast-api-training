from datetime import datetime
from pathlib import Path

import typer

from enums import TaskStatus
from models import Task
from repositories import TaskRepository
from services import TaskService

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
    Format status for better UX with emoji and readable text.

    Args:
        status: TaskStatus enum or string value

    Returns:
        Formatted status string with emoji
    """
    # Convert string to enum if needed
    if isinstance(status, str):
        status = TaskStatus(status)

    # Map status to emoji and formatted text
    status_display = {
        TaskStatus.BACKLOG: "🔵 Backlog",
        TaskStatus.TODO: "📝 To Do",
        TaskStatus.IN_PROGRESS: "🚀 In Progress",
        TaskStatus.TESTING: "🧪 Testing",
        TaskStatus.DONE: "✅ Done",
    }

    return status_display.get(status, status.value.replace("_", " ").title())


def format_datetime(dt: datetime) -> str:
    """
    Format datetime to user's local timezone.

    Args:
        dt: Datetime to format (should be UTC-aware)

    Returns:
        Formatted datetime string in local timezone
    """

    # Convert UTC to local time
    local_dt = dt.astimezone()

    # Format: YYYY-MM-DD HH:MM:SS
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")


def format_datetime_short(dt: datetime) -> str:
    """
    Format datetime to short format in local timezone.

    Args:
        dt: Datetime to format (should be UTC-aware)

    Returns:
        Formatted datetime string (YYYY-MM-DD HH:MM)
    """

    # Convert UTC to local time
    local_dt = dt.astimezone()

    # Short format: YYYY-MM-DD HH:MM
    return local_dt.strftime("%Y-%m-%d %H:%M")


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
    typer.secho(f"✅ {message}", fg=typer.colors.GREEN, bold=True)


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
    typer.secho(f"⚠️  {message}", fg=typer.colors.YELLOW)


def echo_info(message: str, bold: bool = False) -> None:
    """
    Print an info message in cyan.

    Args:
        message: Info message to display
        bold: Whether to make the text bold
    """
    typer.secho(f"ℹ️  {message}", fg=typer.colors.CYAN, bold=bold)


def echo_header(message: str) -> None:
    """
    Print a section header in cyan and bold.

    Args:
        message: Header text to display
    """
    echo()
    typer.secho(f"{'=' * 60}", fg=typer.colors.CYAN, bold=True)
    typer.secho(f"  {message}", fg=typer.colors.CYAN, bold=True)
    typer.secho(f"{'=' * 60}", fg=typer.colors.CYAN, bold=True)


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
    echo()
    echo(f"  ID:          {task.id}")
    echo(f"  Title:       {task.title}")

    if task.description:
        echo(f"  Description: {task.description}")

    echo(f"  Status:      {format_status(task.status)}")

    if show_timestamps:
        echo(f"  Created:     {format_datetime(task.created_at)}")
        echo(f"  Updated:     {format_datetime(task.updated_at)}")


def print_task_created(task: Task) -> None:
    """
    Print task creation success message with details.

    Args:
        task: Newly created task
    """
    echo()
    echo_success("Task created successfully!")
    echo()
    echo_header("📋 Task Details")
    print_task_details(task, show_timestamps=True)
    echo()
    echo(f"{'=' * 60}")
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
    echo()
    echo_header("📋 Task Details")
    print_task_details(task, show_timestamps=True)
    echo()
    echo(f"{'=' * 60}")
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
    echo()
    echo(f"  Title: {title}")
    echo()


def print_task_info(task: Task) -> None:
    """
    Print detailed task information with header.

    Args:
        task: Task to display
    """
    echo()
    echo_header(f"📋 Task #{task.id}")
    print_task_details(task, show_timestamps=True)
    echo()
    echo(f"{'=' * 60}")
    echo()


def print_tasks_table(tasks: list[Task]) -> None:
    """
    Print tasks in a formatted table.

    Args:
        tasks: List of tasks to display
    """
    echo()
    echo_header(f"📋 Tasks ({len(tasks)} total)")
    echo()

    # Table header
    header = f"{'ID':<6} {'Title':<35} {'Status':<18} {'Created':<20}"
    echo(header)
    echo("─" * 80)

    # Table rows
    for task in tasks:
        created_str = format_datetime_short(task.created_at)
        title_display = task.title[:32] + "..." if len(task.title) > 35 else task.title
        status_display = format_status(task.status)

        row = f"{task.id:<6} {title_display:<35} {status_display:<18} {created_str:<20}"
        echo(row)

    echo("─" * 80)
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
        echo_info("No tasks yet. Get started with:")
        echo()
        echo('  uv run task add "Your first task"')
    echo()


def print_summary(stats: dict) -> None:
    """
    Print task summary statistics.

    Args:
        stats: Dictionary containing task statistics
    """
    echo()
    echo_header("📊 Task Summary")
    echo()

    # Total and status breakdown
    echo(f"  Total Tasks:      {stats['total']}")
    echo()
    echo(f"  🔵 Backlog:       {stats['backlog']}")
    echo(f"  📝 To Do:         {stats['todo']}")
    echo(f"  🚀 In Progress:   {stats['in_progress']}")
    echo(f"  🧪 Testing:       {stats['testing']}")
    echo(f"  ✅ Done:          {stats['done']}")
    echo()

    # Additional metrics
    echo(f"  Active Tasks:     {stats['active_tasks']} (TODO, In Progress, Testing)")
    echo(f"  Pending Tasks:    {stats['pending_tasks']} (Backlog, TODO)")
    echo()

    # Completion percentage with color
    completion = stats["completion_percentage"]
    if completion >= 80:
        color = typer.colors.GREEN
    elif completion >= 50:
        color = typer.colors.YELLOW
    else:
        color = typer.colors.RED

    typer.secho(
        f"  📈 Completion:    {completion:.1f}%",
        fg=color,
        bold=True,
    )
    echo()
    echo(f"{'=' * 60}")
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
