# Follow the supporter comments
Fix, explain or ask me if neccessary

Comment: Why do we need this field?
in file: fast_api_practice/src/infrastructure/database/models.py file
```
role: Mapped[str] = mapped_column(
        Enum("user", name="user_role_enum"),
        default="user",
    )
```

Comment: Don't set a default value here. And you should add a startup validator for this.
in file: fast_api_practice/src/core/config.py
```
 # Database
    DATABASE_URL: str = model_config.get(
        "DATABASE_URL",
        "postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice",
    )
    DATABASE_URL_TEST: str = model_config.get(
        "DATABASE_URL_TEST",
        "postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice_test",
    )

    # JWT
    JWT_SECRET_KEY: str = model_config.get("JWT_SECRET_KEY", "")
```

Comment: In the service layer, you should raise ValueError instead. Check and correct other places.
in file: fast_api_practice/src/domain/services/comment_service.py

```
async def create_comment(
        self, task_id: int, author_id: int, content: str
    ) -> CommentEntity:
        task = await self._tasks.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
```

Comment: Check and correct this one
in file: fast_api_practice/src/core/config.py
```
# Database
    DATABASE_URL: str = model_config.get(
        "DATABASE_URL",
        "postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice",
    )
    DATABASE_URL_TEST: str = model_config.get(
        "DATABASE_URL_TEST",
        "postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice_test",
    )

    # JWT
    JWT_SECRET_KEY: str = model_config.get("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = model_config.get("JWT_ALGORITHM, ", "HS256")
```

Comment: This bypasses type safety entirely. Passing an unexpected key sets an arbitrary attribute on the ORM model without error. You should refactor this.
in file: fast_api_practice/src/infrastructure/database/repositories.py
```
async def get_by_email(self, email: str) -> UserEntity | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, id: int, **fields: object) -> UserEntity | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        for key, value in fields.items():
```

Comment: You should validate sort_by first.
in file: fast_api_practice/src/infrastructure/database/repositories.py

```
async def list_for_project(
        self,
        project_id: int,
        *,
        status: TaskStatus | None = None,
        assignee_id: int | None = None,
        priority: TaskPriority | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> list[TaskEntity]:
        sort_col = getattr(TaskModel, sort_by, TaskModel.created_at)
```

