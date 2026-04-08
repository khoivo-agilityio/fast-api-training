"""Integration tests for Comment CRUD API."""

from httpx import AsyncClient

from src.core.security import create_access_token


class TestCommentCRUD:
    async def _setup(self, client: AsyncClient, auth_headers: dict) -> tuple[int, int]:
        """Create a project + task, return (project_id, task_id)."""
        proj_r = await client.post(
            "/api/v1/projects",
            json={"name": "Comment Project"},
            headers=auth_headers,
        )
        project_id = proj_r.json()["id"]
        task_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Comment Task"},
            headers=auth_headers,
        )
        task_id = task_r.json()["id"]
        return project_id, task_id

    async def test_create_comment_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        _, task_id = await self._setup(client, auth_headers)
        r = await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Great work!"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["content"] == "Great work!"
        assert data["task_id"] == task_id

    async def test_create_comment_empty_fails(
        self, client: AsyncClient, auth_headers: dict
    ):
        _, task_id = await self._setup(client, auth_headers)
        r = await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": ""},
            headers=auth_headers,
        )
        assert r.status_code == 422

    async def test_create_comment_non_member_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        _, task_id = await self._setup(client, auth_headers)
        other, _ = await create_test_user(
            username="commentoutsider", email="commentoutsider@example.com"
        )
        other_headers = {"Authorization": f"Bearer {create_access_token(other.id)}"}
        r = await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Hacked!"},
            headers=other_headers,
        )
        assert r.status_code == 403

    async def test_list_comments(self, client: AsyncClient, auth_headers: dict):
        _, task_id = await self._setup(client, auth_headers)
        await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Comment A"},
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Comment B"},
            headers=auth_headers,
        )
        r = await client.get(f"/api/v1/tasks/{task_id}/comments", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        contents = {c["content"] for c in data["items"]}
        assert {"Comment A", "Comment B"} == contents
        assert data["total"] == 2

    async def test_list_comments_nonexistent_task(
        self, client: AsyncClient, auth_headers: dict
    ):
        r = await client.get("/api/v1/tasks/99999/comments", headers=auth_headers)
        assert r.status_code == 404

    async def test_update_own_comment(self, client: AsyncClient, auth_headers: dict):
        _, task_id = await self._setup(client, auth_headers)
        create_r = await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Old text"},
            headers=auth_headers,
        )
        comment_id = create_r.json()["id"]
        r = await client.patch(
            f"/api/v1/tasks/{task_id}/comments/{comment_id}",
            json={"content": "New text"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["content"] == "New text"

    async def test_update_other_users_comment_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        _, task_id = await self._setup(client, auth_headers)
        create_r = await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Original"},
            headers=auth_headers,
        )
        comment_id = create_r.json()["id"]

        member, _ = await create_test_user(
            username="commentmember", email="commentmember@example.com"
        )
        member_headers = {"Authorization": f"Bearer {create_access_token(member.id)}"}
        r = await client.patch(
            f"/api/v1/tasks/{task_id}/comments/{comment_id}",
            json={"content": "Stolen edit"},
            headers=member_headers,
        )
        assert r.status_code == 403

    async def test_delete_own_comment(self, client: AsyncClient, auth_headers: dict):
        _, task_id = await self._setup(client, auth_headers)
        create_r = await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Delete me"},
            headers=auth_headers,
        )
        comment_id = create_r.json()["id"]
        r = await client.delete(
            f"/api/v1/tasks/{task_id}/comments/{comment_id}",
            headers=auth_headers,
        )
        assert r.status_code == 204

    async def test_delete_other_users_comment_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        _, task_id = await self._setup(client, auth_headers)
        create_r = await client.post(
            f"/api/v1/tasks/{task_id}/comments",
            json={"content": "Mine!"},
            headers=auth_headers,
        )
        comment_id = create_r.json()["id"]

        other, _ = await create_test_user(username="thief", email="thief@example.com")
        other_headers = {"Authorization": f"Bearer {create_access_token(other.id)}"}
        r = await client.delete(
            f"/api/v1/tasks/{task_id}/comments/{comment_id}",
            headers=other_headers,
        )
        assert r.status_code == 403
