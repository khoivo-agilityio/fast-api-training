from src.domain.entities.comment import CommentEntity
from src.domain.exceptions import AuthorizationError, NotFoundError
from src.domain.repositories.comment_repository import CommentRepository
from src.domain.repositories.project_repository import ProjectRepository
from src.domain.repositories.task_repository import TaskRepository


class CommentService:
    def __init__(
        self,
        comment_repo: CommentRepository,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
    ) -> None:
        self._comments = comment_repo
        self._tasks = task_repo
        self._projects = project_repo

    async def create_comment(
        self, task_id: int, author_id: int, content: str
    ) -> CommentEntity:
        task = await self._tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        await self._require_project_member(task.project_id, author_id)
        return await self._comments.create(
            content=content, author_id=author_id, task_id=task_id
        )

    async def list_comments(
        self, task_id: int, requester_id: int, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[CommentEntity], int]:
        task = await self._tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        await self._require_project_member(task.project_id, requester_id)
        items = await self._comments.list_for_task(task_id, limit=limit, offset=offset)
        total = await self._comments.count_for_task(task_id)
        return items, total

    async def update_comment(
        self, comment_id: int, requester_id: int, content: str
    ) -> CommentEntity:
        comment = await self._comments.get_by_id(comment_id)
        if comment is None:
            raise NotFoundError("Comment not found")
        if comment.author_id != requester_id:
            raise AuthorizationError("You can only edit your own comments")
        updated = await self._comments.update(comment_id, content)
        if updated is None:
            raise NotFoundError("Comment not found")
        return updated

    async def delete_comment(self, comment_id: int, requester_id: int) -> None:
        comment = await self._comments.get_by_id(comment_id)
        if comment is None:
            raise NotFoundError("Comment not found")
        if comment.author_id != requester_id:
            raise AuthorizationError("You can only delete your own comments")
        await self._comments.delete(comment_id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _require_project_member(self, project_id: int, user_id: int) -> None:
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        if project.owner_id == user_id:
            return
        member = await self._projects.get_member(project_id, user_id)
        if member is None:
            raise AuthorizationError("You are not a member of this project")
