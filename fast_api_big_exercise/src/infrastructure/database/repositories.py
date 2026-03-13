"""SQLAlchemy repository implementations.

Concrete implementations of the repository interfaces using SQLAlchemy ORM.
These live in the infrastructure layer and depend on the database models.
"""

from sqlalchemy.orm import Session

from src.domain.entities.task import Task as TaskEntity
from src.domain.entities.user import User as UserEntity
from src.domain.repositories.task_repository import TaskRepository
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.database.models import TaskModel, UserModel
from src.schemas.task_schemas import TaskPriority, TaskStatus


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user: UserEntity) -> UserEntity:
        """Create a new user in the database."""
        db_user = UserModel(
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            is_active=user.is_active,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_entity(db_user)

    def get_by_id(self, user_id: int) -> UserEntity | None:
        """Get user by ID."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_entity(db_user) if db_user else None

    def get_by_username(self, username: str) -> UserEntity | None:
        """Get user by username."""
        db_user = self.db.query(UserModel).filter(UserModel.username == username).first()
        return self._to_entity(db_user) if db_user else None

    def get_by_email(self, email: str) -> UserEntity | None:
        """Get user by email."""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_entity(db_user) if db_user else None

    def update(self, user: UserEntity) -> UserEntity:
        """Update user in the database."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not db_user:
            raise ValueError(f"User with id {user.id} not found")

        db_user.email = user.email
        db_user.full_name = user.full_name
        db_user.hashed_password = user.hashed_password
        db_user.is_active = user.is_active

        self.db.commit()
        self.db.refresh(db_user)
        return self._to_entity(db_user)

    def delete(self, user_id: int) -> bool:
        """Delete user from the database."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if db_user:
            self.db.delete(db_user)
            self.db.commit()
            return True
        return False

    @staticmethod
    def _to_entity(model: UserModel) -> UserEntity:
        """Convert database model → domain entity."""
        return UserEntity(
            id=model.id,
            username=model.username,
            email=model.email,
            hashed_password=model.hashed_password,
            full_name=model.full_name,
            is_active=model.is_active,
            created_at=model.created_at,
        )


class SQLAlchemyTaskRepository(TaskRepository):
    """SQLAlchemy implementation of TaskRepository."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, task: TaskEntity) -> TaskEntity:
        """Create a new task in the database."""
        db_task = TaskModel(
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            owner_id=task.owner_id,
            due_date=task.due_date,
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return self._to_entity(db_task)

    def get_by_id(self, task_id: int) -> TaskEntity | None:
        """Get task by ID."""
        db_task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
        return self._to_entity(db_task) if db_task else None

    def get_all(
        self,
        owner_id: int,
        skip: int = 0,
        limit: int = 20,
        status: TaskStatus | None = None,
    ) -> list[TaskEntity]:
        """Get all tasks for a user with optional filters."""
        query = self.db.query(TaskModel).filter(TaskModel.owner_id == owner_id)

        if status:
            query = query.filter(TaskModel.status == status.value)

        return [self._to_entity(t) for t in query.offset(skip).limit(limit).all()]

    def count(self, owner_id: int, status: TaskStatus | None = None) -> int:
        """Count tasks for a user."""
        query = self.db.query(TaskModel).filter(TaskModel.owner_id == owner_id)
        if status:
            query = query.filter(TaskModel.status == status.value)
        return query.count()

    def update(self, task: TaskEntity) -> TaskEntity:
        """Update task in the database."""
        db_task = self.db.query(TaskModel).filter(TaskModel.id == task.id).first()
        if not db_task:
            raise ValueError(f"Task with id {task.id} not found")

        db_task.title = task.title
        db_task.description = task.description
        db_task.status = task.status.value
        db_task.priority = task.priority.value
        db_task.due_date = task.due_date

        self.db.commit()
        self.db.refresh(db_task)
        return self._to_entity(db_task)

    def delete(self, task_id: int) -> bool:
        """Delete task from the database."""
        db_task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if db_task:
            self.db.delete(db_task)
            self.db.commit()
            return True
        return False

    @staticmethod
    def _to_entity(model: TaskModel) -> TaskEntity:
        """Convert database model → domain entity."""
        return TaskEntity(
            id=model.id,
            title=model.title,
            description=model.description,
            status=TaskStatus(model.status),
            priority=TaskPriority(model.priority),
            owner_id=model.owner_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            due_date=model.due_date,
        )
