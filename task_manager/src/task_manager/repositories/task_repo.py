import json
from datetime import UTC, datetime
from pathlib import Path

from task_manager.repositories import BaseTaskRepository

from ..enums import TaskStatus
from ..models import Task


class TaskRepository(BaseTaskRepository):
    """JSON file-based task repository implementation"""

    def __init__(self, file_path: str | Path) -> None:
        """
        Initialize the JSON repository.

        Args:
            file_path: Path to the JSON file for storage
        """
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create the JSON file with empty task list if it doesn't exist"""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_tasks([])

    def _read_tasks(self) -> list[Task]:
        """
        Read tasks from JSON file.

        Returns:
            List of tasks from the file
        """
        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []

                tasks = []
                for task_data in data:
                    if "created_at" in task_data:
                        task_data["created_at"] = datetime.fromisoformat(
                            task_data["created_at"]
                        )
                    if "updated_at" in task_data:
                        task_data["updated_at"] = datetime.fromisoformat(
                            task_data["updated_at"]
                        )

                    tasks.append(Task(**task_data))

                return tasks
        except (json.JSONDecodeError, FileNotFoundError, ValueError):
            return []

    def _write_tasks(self, tasks: list[Task]) -> None:
        """
        Write tasks to JSON file.

        Args:
            tasks: List of tasks to write
        """
        with self.file_path.open("w", encoding="utf-8") as f:
            tasks_data = []
            for task in tasks:
                status_value = (
                    task.status.value
                    if isinstance(task.status, TaskStatus)
                    else task.status
                )

                task_dict = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": status_value,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
                tasks_data.append(task_dict)

            json.dump(tasks_data, f, indent=2, ensure_ascii=False)

    def _get_next_id(self, tasks: list[Task]) -> int:
        """
        Get the next available ID.

        Args:
            tasks: Current list of tasks

        Returns:
            Next available ID (max ID + 1, or 1 if no tasks exist)
        """
        if not tasks:
            return 1
        return max(task.id for task in tasks) + 1

    def add(self, task: Task) -> Task:
        """
        Add a new task to the repository.

        Args:
            task: Task to add (ID will be auto-generated)

        Returns:
            Task with assigned ID
        """
        tasks = self._read_tasks()

        new_id = self._get_next_id(tasks)

        new_task = Task(
            id=new_id,
            title=task.title,
            description=task.description,
            status=task.status,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

        tasks.append(new_task)
        self._write_tasks(tasks)

        return new_task

    def list_all(self) -> list[Task]:
        """
        Retrieve all tasks from the repository.

        Returns:
            List of all tasks
        """
        return self._read_tasks()

    def get_by_id(self, task_id: int) -> Task | None:
        """
        Retrieve a task by its ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            Task if found, None otherwise
        """
        tasks = self._read_tasks()
        for task in tasks:
            if task.id == task_id:
                return task
        return None

    def update(self, task: Task) -> Task | None:
        """
        Update an existing task.

        Args:
            task: Task with updated fields

        Returns:
            Updated task if found, None otherwise
        """
        tasks = self._read_tasks()

        for i, existing_task in enumerate(tasks):
            if existing_task.id == task.id:
                updated_task = Task(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    status=task.status,
                    created_at=existing_task.created_at,
                    updated_at=datetime.now(tz=UTC),
                )
                tasks[i] = updated_task
                self._write_tasks(tasks)
                return updated_task

        return None

    def delete(self, task_id: int) -> bool:
        """
        Delete a task by its ID.

        Args:
            task_id: The ID of the task to delete

        Returns:
            True if task was deleted, False if not found
        """
        tasks = self._read_tasks()
        initial_count = len(tasks)

        tasks = [task for task in tasks if task.id != task_id]

        if len(tasks) < initial_count:
            self._write_tasks(tasks)
            return True

        return False
