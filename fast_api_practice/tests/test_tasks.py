"""Integration tests for Task CRUD API."""

from httpx import AsyncClient

from src.core.security import create_access_token


class TestTaskCRUD:
    async def _setup(self, client: AsyncClient, auth_headers: dict) -> tuple[int, dict]:
        """Create a project and return (project_id, auth_headers)."""
        r = await client.post(
            "/api/v1/projects",
            json={"name": "Task Project"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        return r.json()["id"], auth_headers

    async def test_create_task_success(self, client: AsyncClient, auth_headers: dict):
        project_id, headers = await self._setup(client, auth_headers)
        r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "My Task", "description": "do something"},
            headers=headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "My Task"
        assert data["status"] == "todo"
        assert data["priority"] == "medium"
        assert data["project_id"] == project_id
        assert data["is_overdue"] is False

    async def test_create_task_empty_title_fails(
        self, client: AsyncClient, auth_headers: dict
    ):
        project_id, headers = await self._setup(client, auth_headers)
        r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": ""},
            headers=headers,
        )
        assert r.status_code == 422

    async def test_create_task_non_member_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        project_id, _ = await self._setup(client, auth_headers)
        other, _ = await create_test_user(
            username="outsider", email="outsider@example.com"
        )
        other_headers = {
            "Authorization": f"Bearer {create_access_token(other.id, other.role)}"
        }
        r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Intruder task"},
            headers=other_headers,
        )
        assert r.status_code == 403

    async def test_list_tasks_empty(self, client: AsyncClient, auth_headers: dict):
        project_id, headers = await self._setup(client, auth_headers)
        r = await client.get(f"/api/v1/projects/{project_id}/tasks", headers=headers)
        assert r.status_code == 200
        assert r.json() == []

    async def test_list_tasks_with_status_filter(
        self, client: AsyncClient, auth_headers: dict
    ):
        project_id, headers = await self._setup(client, auth_headers)
        await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Todo task", "status": "todo"},
            headers=headers,
        )
        await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Done task", "status": "done"},
            headers=headers,
        )
        r = await client.get(
            f"/api/v1/projects/{project_id}/tasks?status=todo",
            headers=headers,
        )
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["title"] == "Todo task"

    async def test_get_task_success(self, client: AsyncClient, auth_headers: dict):
        project_id, headers = await self._setup(client, auth_headers)
        create_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Get Me"},
            headers=headers,
        )
        task_id = create_r.json()["id"]
        r = await client.get(
            f"/api/v1/projects/{project_id}/tasks/{task_id}", headers=headers
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Get Me"

    async def test_get_task_not_found(self, client: AsyncClient, auth_headers: dict):
        project_id, headers = await self._setup(client, auth_headers)
        r = await client.get(
            f"/api/v1/projects/{project_id}/tasks/99999", headers=headers
        )
        assert r.status_code == 404

    async def test_update_task_status(self, client: AsyncClient, auth_headers: dict):
        project_id, headers = await self._setup(client, auth_headers)
        create_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Progress Task"},
            headers=headers,
        )
        task_id = create_r.json()["id"]
        r = await client.patch(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            json={"status": "in_progress"},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["status"] == "in_progress"

    async def test_update_task_priority(self, client: AsyncClient, auth_headers: dict):
        project_id, headers = await self._setup(client, auth_headers)
        create_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "High Prio Task"},
            headers=headers,
        )
        task_id = create_r.json()["id"]
        r = await client.patch(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            json={"priority": "high"},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["priority"] == "high"

    async def test_assign_task_to_member(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        project_id, headers = await self._setup(client, auth_headers)
        member, _ = await create_test_user(
            username="assignee", email="assignee@example.com"
        )
        # Add member to project
        await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": member.id},
            headers=headers,
        )
        create_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Assigned Task"},
            headers=headers,
        )
        task_id = create_r.json()["id"]
        r = await client.patch(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            json={"assignee_id": member.id},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.json()["assignee_id"] == member.id

    async def test_assign_task_to_non_member_fails(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        project_id, headers = await self._setup(client, auth_headers)
        outsider, _ = await create_test_user(username="nope", email="nope@example.com")
        create_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Assign Fail"},
            headers=headers,
        )
        task_id = create_r.json()["id"]
        r = await client.patch(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            json={"assignee_id": outsider.id},
            headers=headers,
        )
        assert r.status_code == 403

    async def test_delete_task_success(self, client: AsyncClient, auth_headers: dict):
        project_id, headers = await self._setup(client, auth_headers)
        create_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Delete Me"},
            headers=headers,
        )
        task_id = create_r.json()["id"]
        r = await client.delete(
            f"/api/v1/projects/{project_id}/tasks/{task_id}", headers=headers
        )
        assert r.status_code == 204

    async def test_delete_task_non_member_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        project_id, headers = await self._setup(client, auth_headers)
        create_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "No Delete"},
            headers=headers,
        )
        task_id = create_r.json()["id"]
        other, _ = await create_test_user(
            username="nodeleter", email="nodeleter@example.com"
        )
        other_headers = {
            "Authorization": f"Bearer {create_access_token(other.id, other.role)}"
        }
        r = await client.delete(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            headers=other_headers,
        )
        assert r.status_code == 403
