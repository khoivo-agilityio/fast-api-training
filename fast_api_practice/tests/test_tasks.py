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
        data = r.json()
        assert data["items"] == []
        assert data["total"] == 0

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
        data = r.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Todo task"

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

    async def test_get_task_wrong_project(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Task ID exists but belongs to a different project — must return 404."""
        project_id, headers = await self._setup(client, auth_headers)
        # Create a second project and a task in it
        other_project_r = await client.post(
            "/api/v1/projects",
            json={"name": "Other Project"},
            headers=headers,
        )
        other_project_id = other_project_r.json()["id"]
        task_r = await client.post(
            f"/api/v1/projects/{other_project_id}/tasks",
            json={"title": "Other Task"},
            headers=headers,
        )
        task_id = task_r.json()["id"]
        # Try to fetch the task under the wrong project
        r = await client.get(
            f"/api/v1/projects/{project_id}/tasks/{task_id}", headers=headers
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


class TestTaskRBAC:
    """RBAC hardening tests for task update/delete."""

    async def _setup_with_member(
        self, client: AsyncClient, auth_headers: dict, create_test_user
    ) -> tuple[int, int, dict]:
        """Create project+task as owner; add a plain member.

        Returns (project_id, task_id, member_headers).
        """
        proj_r = await client.post(
            "/api/v1/projects", json={"name": "RBAC Project"}, headers=auth_headers
        )
        project_id = proj_r.json()["id"]
        task_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "RBAC Task"},
            headers=auth_headers,
        )
        task_id = task_r.json()["id"]
        member, _ = await create_test_user(
            username="plain_member", email="plain_member@example.com"
        )
        await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": member.id, "role": "member"},
            headers=auth_headers,
        )
        member_headers = {
            "Authorization": f"Bearer {create_access_token(member.id, member.role)}"
        }
        return project_id, task_id, member_headers

    async def test_plain_member_cannot_update_task(
        self, client: AsyncClient, auth_headers: dict, create_test_user
    ):
        project_id, task_id, member_headers = await self._setup_with_member(
            client, auth_headers, create_test_user
        )
        r = await client.patch(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            json={"title": "Stolen update"},
            headers=member_headers,
        )
        assert r.status_code == 403

    async def test_plain_member_cannot_delete_task(
        self, client: AsyncClient, auth_headers: dict, create_test_user
    ):
        project_id, task_id, member_headers = await self._setup_with_member(
            client, auth_headers, create_test_user
        )
        r = await client.delete(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            headers=member_headers,
        )
        assert r.status_code == 403

    async def test_assignee_can_update_task(
        self, client: AsyncClient, auth_headers: dict, create_test_user
    ):
        proj_r = await client.post(
            "/api/v1/projects", json={"name": "Assignee Project"}, headers=auth_headers
        )
        project_id = proj_r.json()["id"]
        assignee, _ = await create_test_user(
            username="assignee2", email="assignee2@example.com"
        )
        await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": assignee.id},
            headers=auth_headers,
        )
        task_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Assigned Task", "assignee_id": assignee.id},
            headers=auth_headers,
        )
        task_id = task_r.json()["id"]
        assignee_headers = {
            "Authorization": f"Bearer {create_access_token(assignee.id, assignee.role)}"
        }
        r = await client.patch(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            json={"title": "Updated by assignee"},
            headers=assignee_headers,
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Updated by assignee"

    async def test_project_admin_can_update_any_task(
        self, client: AsyncClient, auth_headers: dict, create_test_user
    ):
        proj_r = await client.post(
            "/api/v1/projects", json={"name": "Admin Project"}, headers=auth_headers
        )
        project_id = proj_r.json()["id"]
        admin_user, _ = await create_test_user(
            username="proj_admin", email="proj_admin@example.com"
        )
        await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": admin_user.id, "role": "admin"},
            headers=auth_headers,
        )
        task_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Task for admin"},
            headers=auth_headers,
        )
        task_id = task_r.json()["id"]
        token = create_access_token(admin_user.id, admin_user.role)
        admin_hdrs = {"Authorization": f"Bearer {token}"}
        r = await client.patch(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            json={"title": "Admin updated"},
            headers=admin_hdrs,
        )
        assert r.status_code == 200

    async def test_project_admin_can_delete_any_task(
        self, client: AsyncClient, auth_headers: dict, create_test_user
    ):
        proj_r = await client.post(
            "/api/v1/projects",
            json={"name": "Admin Delete Project"},
            headers=auth_headers,
        )
        project_id = proj_r.json()["id"]
        admin_user, _ = await create_test_user(
            username="proj_admin2", email="proj_admin2@example.com"
        )
        await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": admin_user.id, "role": "admin"},
            headers=auth_headers,
        )
        task_r = await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Task to delete"},
            headers=auth_headers,
        )
        task_id = task_r.json()["id"]
        token = create_access_token(admin_user.id, admin_user.role)
        admin_hdrs = {"Authorization": f"Bearer {token}"}
        r = await client.delete(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            headers=admin_hdrs,
        )
        assert r.status_code == 204


class TestTaskPagination:
    async def test_list_tasks_pagination(self, client: AsyncClient, auth_headers: dict):
        proj_r = await client.post(
            "/api/v1/projects", json={"name": "Paginate Project"}, headers=auth_headers
        )
        project_id = proj_r.json()["id"]
        for i in range(5):
            await client.post(
                f"/api/v1/projects/{project_id}/tasks",
                json={"title": f"Task{i}"},
                headers=auth_headers,
            )
        r = await client.get(
            f"/api/v1/projects/{project_id}/tasks?limit=2&offset=0",
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2

    async def test_list_tasks_priority_filter(
        self, client: AsyncClient, auth_headers: dict
    ):
        proj_r = await client.post(
            "/api/v1/projects", json={"name": "Priority Project"}, headers=auth_headers
        )
        project_id = proj_r.json()["id"]
        await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "High task", "priority": "high"},
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Low task", "priority": "low"},
            headers=auth_headers,
        )
        r = await client.get(
            f"/api/v1/projects/{project_id}/tasks?priority=high",
            headers=auth_headers,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["priority"] == "high"
