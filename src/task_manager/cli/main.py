from pathlib import Path
from typing import Annotated

import typer

from ..models import TaskStatus
from .helpers import (
    get_service,
    handle_error,
    print_no_tasks,
    print_summary,
    print_task_created,
    print_task_deleted,
    print_task_info,
    print_task_updated,
    print_tasks_table,
)

# Initialize Typer app
app = typer.Typer(
    name="task",
    help="Task Manager - Manage your tasks efficiently from the command line",
)


# ============================================================================
# CLI COMMANDS
# ============================================================================


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
    Add a new task with BACKLOG status.

    Example:
        task add "Write unit tests"
        task add "Review PR" -d "Check code quality and tests"
    """
    try:
        service = get_service(data_file)
        desc = description if description else None
        task = service.add_task(title=title, description=desc)
        print_task_created(task)

    except ValueError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@app.command()
def update(
    task_id: Annotated[int, typer.Argument(help="Task ID to update")],
    title: Annotated[
        str | None, typer.Option("--title", "-t", help="New task title")
    ] = None,
    description: Annotated[
        str | None, typer.Option("--description", "-d", help="New task description")
    ] = None,
    status: Annotated[
        str | None, typer.Option("--status", "-s", help="New task status")
    ] = None,
    data_file: Annotated[
        Path | None, typer.Option("--file", "-f", help="Custom data file path")
    ] = None,
) -> None:
    """
    Update a task's title, description, or status.

    Example:
        task update 1 --title "New title"
        task update 1 -s todo
        task update 1 -t "Updated" -d "New description" -s in-progress
    """
    try:
        service = get_service(data_file)

        # Parse status if provided
        status_enum = None
        if status:
            try:
                normalized_status = status.lower().replace("-", "_")
                status_enum = TaskStatus(normalized_status)
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                handle_error(
                    ValueError(
                        f"Invalid status: '{status}'. "
                        f"Valid statuses: {', '.join(valid_statuses)}"
                    )
                )

        # Update the task
        updated_task = service.update_task(
            task_id=task_id,
            title=title,
            description=description,
            status=status_enum,
        )

        print_task_updated(updated_task)

    except ValueError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@app.command()
def done(
    task_id: Annotated[int, typer.Argument(help="Task ID to mark as done")],
    data_file: Annotated[
        Path | None, typer.Option("--file", "-f", help="Custom data file path")
    ] = None,
) -> None:
    """
    Mark a task as DONE.

    Example:
        task done 1
    """
    try:
        service = get_service(data_file)
        updated_task = service.mark_as_done(task_id)
        print_task_updated(updated_task, action="marked as done")

    except ValueError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@app.command()
def remove(
    task_id: Annotated[int, typer.Argument(help="Task ID to delete")],
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Skip confirmation")
    ] = False,
    data_file: Annotated[
        Path | None, typer.Option("--file", help="Custom data file path")
    ] = None,
) -> None:
    """
    Delete a task permanently.

    Example:
        task remove 1
        task remove 1 --force
    """
    try:
        service = get_service(data_file)

        # Get task details for confirmation
        task = service.get_task(task_id)

        # Ask for confirmation unless --force is used
        if not force:
            confirm = typer.confirm(
                f"Are you sure you want to delete task #{task_id}: '{task.title}'?"
            )
            if not confirm:
                typer.echo("Deletion cancelled.")
                raise typer.Abort()

        # Delete the task
        service.delete_task(task_id)
        print_task_deleted(task_id, task.title)

    except ValueError as e:
        handle_error(e)
    except typer.Abort:
        raise
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
    List all tasks or filter by status.

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
            print_no_tasks(status_filter)
            return

        print_tasks_table(tasks)

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
    Show detailed information about a specific task.

    Example:
        task show 1
    """
    try:
        service = get_service(data_file)
        task = service.get_task(task_id)
        print_task_info(task)

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
    Display task statistics and completion progress.

    Example:
        task summary
    """
    try:
        service = get_service(data_file)
        stats = service.get_summary()
        print_summary(stats)

    except Exception as e:
        handle_error(e)
