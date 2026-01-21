"""Task Manager CLI - Command-line interface for task management"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from ..models import TaskStatus
from ..services import TaskService
from ..storage.json_repo import JsonTaskRepository

# Initialize Typer app
app = typer.Typer(
    name="task",
    help="📋 Task Manager - Manage your tasks efficiently from the command line",
    add_completion=False,
)

# Rich console for beautiful output
console = Console()

# Default data file location
DEFAULT_DATA_FILE = Path.home() / ".task_manager" / "tasks.json"


def get_service(data_file: Path | None = None) -> TaskService:
    """Get TaskService instance with configured repository."""
    file_path = data_file or DEFAULT_DATA_FILE
    repository = JsonTaskRepository(file_path)
    return TaskService(repository)


def format_status(status: TaskStatus) -> str:
    """Format status with emoji for better UX."""
    status_emojis = {
        TaskStatus.BACKLOG: "📋",
        TaskStatus.TODO: "📝",
        TaskStatus.IN_PROGRESS: "🔄",
        TaskStatus.TESTING: "🧪",
        TaskStatus.DONE: "✅",
    }
    emoji = status_emojis.get(status, "📌")
    return f"{emoji} {status.value.upper().replace('_', ' ')}"


def handle_error(error: Exception) -> None:
    """Handle and display errors gracefully."""
    console.print(f"[bold red]Error:[/bold red] {str(error)}")
    raise typer.Exit(code=1)


@app.command()
def add(
    title: Annotated[str, typer.Argument(help="Task title (required)")],
    description: Annotated[
        str, typer.Option("--description", "-d", help="Task description")
    ] = "",
    data_file: Annotated[
        Path | None, typer.Option("--file", "-f", help="Custom data file path")
    ] = None,
) -> None:
    """
    ➕ Add a new task with BACKLOG status.

    Example:
        task add "Write unit tests"
        task add "Review PR" -d "Check code quality and tests"
    """
    try:
        service = get_service(data_file)
        desc = description if description else None
        task = service.add_task(title=title, description=desc)

        console.print("\n[bold green]✓ Task created successfully![/bold green]")
        console.print(f"[cyan]ID:[/cyan] {task.id}")
        console.print(f"[cyan]Title:[/cyan] {task.title}")
        if task.description:
            console.print(f"[cyan]Description:[/cyan] {task.description}")
        console.print(f"[cyan]Status:[/cyan] {format_status(task.status)}")
        console.print()

    except ValueError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@app.command(name="list")
def list_tasks(
    status: Annotated[
        str, typer.Option("--status", "-s", help="Filter by status")
    ] = "",
    data_file: Annotated[
        Path | None, typer.Option("--file", "-f", help="Custom data file path")
    ] = None,
) -> None:
    """
    📋 List all tasks or filter by status.

    Example:
        task list
        task list --status todo
        task list -s done
    """
    try:
        service = get_service(data_file)

        # Parse status filter if provided
        status_filter = None
        if status:
            try:
                normalized_status = status.lower().replace("-", "_")
                status_filter = TaskStatus(normalized_status)
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                handle_error(
                    ValueError(
                        f"Invalid status: '{status}'. "
                        f"Valid statuses: {', '.join(valid_statuses)}"
                    )
                )

        tasks = service.list_tasks(status=status_filter)

        if not tasks:
            if status_filter:
                console.print(
                    f"\n[yellow]No tasks found with status: "
                    f"{format_status(status_filter)}[/yellow]\n"
                )
            else:
                console.print("\n[yellow]No tasks yet. Add one with:[/yellow]")
                console.print('[cyan]  task add "Your first task"[/cyan]\n')
            return

        # Create table
        table = Table(title=f"📋 Tasks ({len(tasks)} total)", show_header=True)
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Title", style="white", width=40)
        table.add_column("Status", width=20)
        table.add_column("Created", style="dim", width=20)

        for task in tasks:
            created_str = task.created_at.strftime("%Y-%m-%d %H:%M")
            table.add_row(
                str(task.id),
                task.title[:37] + "..." if len(task.title) > 40 else task.title,
                format_status(task.status),
                created_str,
            )

        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        handle_error(e)


@app.command()
def show(
    task_id: Annotated[int, typer.Argument(help="Task ID to display")],
    data_file: Annotated[
        Path | None, typer.Option("--file", "-f", help="Custom data file path")
    ] = None,
) -> None:
    """
    🔍 Show detailed information about a specific task.

    Example:
        task show 1
    """
    try:
        service = get_service(data_file)
        task = service.get_task(task_id)

        console.print()
        console.print(f"[bold cyan]Task #{task.id}[/bold cyan]")
        console.print(f"[cyan]Title:[/cyan] {task.title}")
        console.print(f"[cyan]Status:[/cyan] {format_status(task.status)}")
        if task.description:
            console.print(f"[cyan]Description:[/cyan] {task.description}")
        console.print(
            f"[cyan]Created:[/cyan] {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        console.print(
            f"[cyan]Updated:[/cyan] {task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        console.print()

    except ValueError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@app.command()
def summary(
    data_file: Annotated[
        Path | None, typer.Option("--file", "-f", help="Custom data file path")
    ] = None,
) -> None:
    """
    📊 Display task statistics and completion progress.

    Example:
        task summary
    """
    try:
        service = get_service(data_file)
        stats = service.get_summary()

        console.print("\n[bold cyan]📊 Task Summary[/bold cyan]\n")
        console.print(f"[cyan]Total Tasks:[/cyan] {stats['total']}")
        console.print(f"📋 Backlog: {stats['backlog']}")
        console.print(f"📝 To Do: {stats['todo']}")
        console.print(f"🔄 In Progress: {stats['in_progress']}")
        console.print(f"🧪 Testing: {stats['testing']}")
        console.print(f"✅ Done: {stats['done']}")
        console.print(
            "\n[bold green]Completion: "
            f"{stats['completion_percentage']:.1f}%[/bold green]\n"
        )

    except Exception as e:
        handle_error(e)


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    app()
