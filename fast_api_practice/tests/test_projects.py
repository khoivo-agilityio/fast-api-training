"""Integration tests for Project CRUD and Members API."""

from httpx import AsyncClient


class TestProjectCRUD:
    async def test_create_project_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        r = await client.post(
            "/api/v1/projects",
            json={"name": "Alpha", "description": "First project"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Alpha"
        assert data["description"] == "First project"
        assert "id" in data
        assert "owner_id" in data

    async def test_create_project_no_auth(self, client: AsyncClient):
        r = await client.post("/api/v1/projects", json={"name": "X"})
        assert r.status_code in (401, 403)  # unauthenticated request

    async def test_create_project_empty_name(
        self, client: AsyncClient, auth_headers: dict
    ):
        r = await client.post(
            "/api/v1/projects", json={"name": ""}, headers=auth_headers
        )
        assert r.status_code == 422

    async def test_list_projects_empty(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/api/v1/projects", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_projects_shows_owned(
        self, client: AsyncClient, auth_headers: dict
    ):
        await client.post("/api/v1/projects", json={"name": "P1"}, headers=auth_headers)
        await client.post("/api/v1/projects", json={"name": "P2"}, headers=auth_headers)
        r = await client.get("/api/v1/projects", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        names = {p["name"] for p in data["items"]}
        assert {"P1", "P2"} == names
        assert data["total"] == 2

    async def test_get_project_success(self, client: AsyncClient, auth_headers: dict):
        create_r = await client.post(
            "/api/v1/projects", json={"name": "Beta"}, headers=auth_headers
        )
        project_id = create_r.json()["id"]
        r = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["name"] == "Beta"

    async def test_get_project_not_found(self, client: AsyncClient, auth_headers: dict):
        r = await client.get("/api/v1/projects/99999", headers=auth_headers)
        assert r.status_code == 404

    async def test_update_project_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        create_r = await client.post(
            "/api/v1/projects", json={"name": "Old Name"}, headers=auth_headers
        )
        project_id = create_r.json()["id"]
        r = await client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["name"] == "New Name"

    async def test_update_project_non_manager_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        from src.core.security import create_access_token

        create_r = await client.post(
            "/api/v1/projects", json={"name": "Owner Project"}, headers=auth_headers
        )
        project_id = create_r.json()["id"]

        other_user, _ = await create_test_user(
            username="other", email="other@example.com"
        )
        other_token = create_access_token(other_user.id, other_user.role)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        r = await client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "Hijack"},
            headers=other_headers,
        )
        assert r.status_code == 403

    async def test_delete_project_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        create_r = await client.post(
            "/api/v1/projects", json={"name": "ToDelete"}, headers=auth_headers
        )
        project_id = create_r.json()["id"]
        r = await client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert r.status_code == 204

        # Confirm gone
        r2 = await client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
        assert r2.status_code == 404

    async def test_delete_project_non_owner_forbidden(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        from src.core.security import create_access_token

        create_r = await client.post(
            "/api/v1/projects", json={"name": "Protected"}, headers=auth_headers
        )
        project_id = create_r.json()["id"]

        other_user, _ = await create_test_user(
            username="other2", email="other2@example.com"
        )
        other_token = create_access_token(other_user.id, other_user.role)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        r = await client.delete(f"/api/v1/projects/{project_id}", headers=other_headers)
        assert r.status_code == 403

    async def test_project_admin_can_delete_project(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        """A user promoted to project admin (not owner) can delete."""
        from src.core.security import create_access_token

        create_r = await client.post(
            "/api/v1/projects",
            json={"name": "AdminTarget"},
            headers=auth_headers,
        )
        project_id = create_r.json()["id"]

        admin_user, _ = await create_test_user(
            username="projadmin", email="projadmin@example.com"
        )
        # Add as member then promote to admin
        await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": admin_user.id, "role": "admin"},
            headers=auth_headers,
        )
        admin_token = create_access_token(admin_user.id, admin_user.role)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        r = await client.delete(f"/api/v1/projects/{project_id}", headers=admin_headers)
        assert r.status_code == 204

    async def test_list_projects_pagination(
        self, client: AsyncClient, auth_headers: dict
    ):
        for i in range(5):
            await client.post(
                "/api/v1/projects", json={"name": f"Proj{i}"}, headers=auth_headers
            )
        # First page of 2
        r = await client.get("/api/v1/projects?limit=2&offset=0", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0
        # Second page
        r2 = await client.get("/api/v1/projects?limit=2&offset=2", headers=auth_headers)
        data2 = r2.json()
        assert len(data2["items"]) == 2
        # Third page (1 item left)
        r3 = await client.get("/api/v1/projects?limit=2&offset=4", headers=auth_headers)
        data3 = r3.json()
        assert len(data3["items"]) == 1


class TestProjectMembers:
    async def _create_project(
        self, client: AsyncClient, headers: dict, name: str = "Test Project"
    ) -> int:
        r = await client.post("/api/v1/projects", json={"name": name}, headers=headers)
        assert r.status_code == 201
        return r.json()["id"]

    async def test_add_member_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        project_id = await self._create_project(client, auth_headers)
        other_user, _ = await create_test_user(
            username="newmember", email="newmember@example.com"
        )
        r = await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": other_user.id, "role": "member"},
            headers=auth_headers,
        )
        assert r.status_code == 201
        assert r.json()["user_id"] == other_user.id
        assert r.json()["role"] == "member"

    async def test_add_member_duplicate_fails(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        project_id = await self._create_project(client, auth_headers)
        other_user, _ = await create_test_user(username="dup", email="dup@example.com")
        await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": other_user.id},
            headers=auth_headers,
        )
        r = await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": other_user.id},
            headers=auth_headers,
        )
        assert r.status_code == 409

    async def test_add_nonexistent_user_fails(
        self, client: AsyncClient, auth_headers: dict
    ):
        project_id = await self._create_project(client, auth_headers)
        r = await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": 99999},
            headers=auth_headers,
        )
        assert r.status_code == 404

    async def test_list_members(
        self, client: AsyncClient, auth_headers: dict, create_test_user
    ):
        project_id = await self._create_project(client, auth_headers)
        other_user, _ = await create_test_user(
            username="listme", email="listme@example.com"
        )
        await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": other_user.id},
            headers=auth_headers,
        )
        r = await client.get(
            f"/api/v1/projects/{project_id}/members", headers=auth_headers
        )
        assert r.status_code == 200
        # owner (manager) + new member
        assert len(r.json()) == 2

    async def test_update_member_role(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        project_id = await self._create_project(client, auth_headers)
        other_user, _ = await create_test_user(
            username="promote", email="promote@example.com"
        )
        await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": other_user.id, "role": "member"},
            headers=auth_headers,
        )
        r = await client.patch(
            f"/api/v1/projects/{project_id}/members/{other_user.id}",
            json={"role": "admin"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["role"] == "admin"

    async def test_remove_member_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        create_test_user,
    ):
        project_id = await self._create_project(client, auth_headers)
        other_user, _ = await create_test_user(
            username="removeme", email="removeme@example.com"
        )
        await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": other_user.id},
            headers=auth_headers,
        )
        r = await client.delete(
            f"/api/v1/projects/{project_id}/members/{other_user.id}",
            headers=auth_headers,
        )
        assert r.status_code == 204

    async def test_remove_owner_forbidden(
        self, client: AsyncClient, auth_headers: dict
    ):
        project_id = await self._create_project(client, auth_headers)

        # Get owner's user_id from the members list
        members_r = await client.get(
            f"/api/v1/projects/{project_id}/members", headers=auth_headers
        )
        owner_member = next(m for m in members_r.json() if m["role"] == "admin")
        owner_id = owner_member["user_id"]

        r = await client.delete(
            f"/api/v1/projects/{project_id}/members/{owner_id}",
            headers=auth_headers,
        )
        assert r.status_code == 403
