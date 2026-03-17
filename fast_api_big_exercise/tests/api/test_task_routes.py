"""Integration tests for /api/v1/tasks/* endpoints."""

from fastapi.testclient import TestClient

from tests.base import BaseIntegrationTestCase
from tests.fixtures import BOB

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE = "/api/v1/tasks"

_TASK_1 = {
    "title": "Buy groceries",
    "description": "Milk, bread, eggs",
    "status": "todo",
    "priority": "medium",
}

_TASK_2 = {
    "title": "Write tests",
    "status": "in_progress",
    "priority": "high",
}


class TestCreateTask(BaseIntegrationTestCase):
    """POST /api/v1/tasks"""

    def test_create_task_success(self, client: TestClient, auth_headers: dict) -> None:
        """Authenticated user can create a task."""
        resp = client.post(_BASE, json=_TASK_1, headers=auth_headers)
        self.assert_http(resp, 201)
        body = resp.json()
        assert body["title"] == _TASK_1["title"]
        assert body["description"] == _TASK_1["description"]
        assert body["status"] == "todo"
        assert body["priority"] == "medium"
        assert "id" in body
        assert "created_at" in body

    def test_create_task_minimal(self, client: TestClient, auth_headers: dict) -> None:
        """Only title is required; all other fields have defaults."""
        resp = client.post(_BASE, json={"title": "Minimal task"}, headers=auth_headers)
        self.assert_http(resp, 201)
        body = resp.json()
        assert body["title"] == "Minimal task"
        assert body["status"] == "todo"
        assert body["priority"] == "medium"
        assert body["description"] is None

    def test_create_task_unauthenticated(self, client: TestClient) -> None:
        """Unauthenticated request returns 401."""
        resp = client.post(_BASE, json=_TASK_1)
        self.assert_http(resp, 401)

    def test_create_task_empty_title(self, client: TestClient, auth_headers: dict) -> None:
        """Empty title returns 422."""
        resp = client.post(_BASE, json={"title": ""}, headers=auth_headers)
        self.assert_validation_error(resp, "title")

    def test_create_task_missing_title(self, client: TestClient, auth_headers: dict) -> None:
        """Missing title returns 422."""
        resp = client.post(_BASE, json={"description": "no title"}, headers=auth_headers)
        self.assert_validation_error(resp)

    def test_create_task_invalid_status(self, client: TestClient, auth_headers: dict) -> None:
        """Invalid status value returns 422."""
        resp = client.post(_BASE, json={**_TASK_1, "status": "flying"}, headers=auth_headers)
        self.assert_validation_error(resp)

    def test_create_task_invalid_priority(self, client: TestClient, auth_headers: dict) -> None:
        """Invalid priority value returns 422."""
        resp = client.post(_BASE, json={**_TASK_1, "priority": "extreme"}, headers=auth_headers)
        self.assert_validation_error(resp)

    def test_create_task_with_due_date(self, client: TestClient, auth_headers: dict) -> None:
        """Task can be created with an ISO 8601 due date."""
        resp = client.post(
            _BASE,
            json={**_TASK_1, "due_date": "2030-01-01T00:00:00Z"},
            headers=auth_headers,
        )
        self.assert_http(resp, 201)
        assert resp.json()["due_date"] is not None

    def test_tasks_are_scoped_to_owner(self, client: TestClient, auth_headers: dict) -> None:
        """A task's owner_id matches the authenticated user's id."""
        # Register and login as Alice (auth_headers fixture already does this)
        me_resp = client.get("/api/v1/auth/me", headers=auth_headers)
        alice_id = me_resp.json()["id"]

        task_resp = client.post(_BASE, json=_TASK_1, headers=auth_headers)
        assert task_resp.json()["owner_id"] == alice_id


class TestListTasks(BaseIntegrationTestCase):
    """GET /api/v1/tasks"""

    def _create(self, client: TestClient, headers: dict, payload: dict) -> dict:  # type: ignore[type-arg]
        return client.post(_BASE, json=payload, headers=headers).json()

    def test_list_tasks_empty(self, client: TestClient, auth_headers: dict) -> None:
        """New user has no tasks."""
        resp = client.get(_BASE, headers=auth_headers)
        self.assert_http(resp, 200)
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_list_tasks_returns_own_tasks(self, client: TestClient, auth_headers: dict) -> None:
        """Listed tasks belong to the authenticated user."""
        self._create(client, auth_headers, _TASK_1)
        self._create(client, auth_headers, _TASK_2)
        resp = client.get(_BASE, headers=auth_headers)
        self.assert_http(resp, 200)
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_list_tasks_isolation(self, client: TestClient, auth_headers: dict) -> None:
        """User B cannot see User A's tasks."""
        # Alice creates a task
        self._create(client, auth_headers, _TASK_1)

        # Register and login as Bob
        client.post("/api/v1/auth/register", json=BOB)
        bob_token = client.post(
            "/api/v1/auth/login",
            data={"username": BOB["username"], "password": BOB["password"]},
        ).json()["access_token"]
        bob_headers = self.bearer(bob_token)

        resp = client.get(_BASE, headers=bob_headers)
        assert resp.json()["total"] == 0

    def test_list_tasks_filter_by_status(self, client: TestClient, auth_headers: dict) -> None:
        """Status filter returns only matching tasks."""
        self._create(client, auth_headers, {**_TASK_1, "status": "todo"})
        self._create(client, auth_headers, {**_TASK_2, "status": "in_progress"})

        resp = client.get(_BASE, params={"status": "todo"}, headers=auth_headers)
        self.assert_http(resp, 200)
        items = resp.json()["items"]
        assert all(t["status"] == "todo" for t in items)

    def test_list_tasks_pagination(self, client: TestClient, auth_headers: dict) -> None:
        """Pagination parameters are respected."""
        for i in range(5):
            self._create(client, auth_headers, {"title": f"Task {i}"})

        resp_p1 = client.get(_BASE, params={"page": 1, "size": 2}, headers=auth_headers)
        resp_p2 = client.get(_BASE, params={"page": 2, "size": 2}, headers=auth_headers)

        self.assert_http(resp_p1, 200)
        self.assert_http(resp_p2, 200)

        p1 = resp_p1.json()
        p2 = resp_p2.json()
        assert p1["total"] == 5
        assert len(p1["items"]) == 2
        assert len(p2["items"]) == 2
        # Items on different pages must differ
        p1_ids = {t["id"] for t in p1["items"]}
        p2_ids = {t["id"] for t in p2["items"]}
        assert p1_ids.isdisjoint(p2_ids)

    def test_list_tasks_unauthenticated(self, client: TestClient) -> None:
        """Unauthenticated request returns 401."""
        resp = client.get(_BASE)
        self.assert_http(resp, 401)

    def test_list_tasks_invalid_page(self, client: TestClient, auth_headers: dict) -> None:
        """page < 1 returns 422."""
        resp = client.get(_BASE, params={"page": 0}, headers=auth_headers)
        self.assert_validation_error(resp)

    def test_list_tasks_invalid_size(self, client: TestClient, auth_headers: dict) -> None:
        """size > 100 returns 422."""
        resp = client.get(_BASE, params={"size": 200}, headers=auth_headers)
        self.assert_validation_error(resp)


class TestGetTask(BaseIntegrationTestCase):
    """GET /api/v1/tasks/{task_id}"""

    def _create_task(self, client: TestClient, headers: dict) -> dict:  # type: ignore[type-arg]
        return client.post(_BASE, json=_TASK_1, headers=headers).json()

    def test_get_task_success(self, client: TestClient, auth_headers: dict) -> None:
        """Owner can fetch their task by ID."""
        created = self._create_task(client, auth_headers)
        resp = client.get(f"{_BASE}/{created['id']}", headers=auth_headers)
        self.assert_http(resp, 200)
        assert resp.json()["id"] == created["id"]
        assert resp.json()["title"] == _TASK_1["title"]

    def test_get_task_not_found(self, client: TestClient, auth_headers: dict) -> None:
        """Non-existent task ID returns 404."""
        resp = client.get(f"{_BASE}/99999", headers=auth_headers)
        self.assert_http(resp, 404)

    def test_get_task_wrong_owner(self, client: TestClient, auth_headers: dict) -> None:
        """Bob cannot access Alice's task."""
        created = self._create_task(client, auth_headers)

        client.post("/api/v1/auth/register", json=BOB)
        bob_token = client.post(
            "/api/v1/auth/login",
            data={"username": BOB["username"], "password": BOB["password"]},
        ).json()["access_token"]
        bob_headers = self.bearer(bob_token)

        resp = client.get(f"{_BASE}/{created['id']}", headers=bob_headers)
        assert resp.status_code in (403, 404)

    def test_get_task_unauthenticated(self, client: TestClient) -> None:
        """Unauthenticated request returns 401."""
        resp = client.get(f"{_BASE}/1")
        self.assert_http(resp, 401)


class TestUpdateTask(BaseIntegrationTestCase):
    """PATCH /api/v1/tasks/{task_id}"""

    def _create_task(self, client: TestClient, headers: dict) -> dict:  # type: ignore[type-arg]
        return client.post(_BASE, json=_TASK_1, headers=headers).json()

    def test_update_task_title(self, client: TestClient, auth_headers: dict) -> None:
        """Owner can update a task's title."""
        created = self._create_task(client, auth_headers)
        resp = client.patch(
            f"{_BASE}/{created['id']}",
            json={"title": "Updated title"},
            headers=auth_headers,
        )
        self.assert_http(resp, 200)
        assert resp.json()["title"] == "Updated title"

    def test_update_task_status(self, client: TestClient, auth_headers: dict) -> None:
        """Owner can change a task's status."""
        created = self._create_task(client, auth_headers)
        resp = client.patch(
            f"{_BASE}/{created['id']}",
            json={"status": "done"},
            headers=auth_headers,
        )
        self.assert_http(resp, 200)
        assert resp.json()["status"] == "done"

    def test_update_task_partial(self, client: TestClient, auth_headers: dict) -> None:
        """Patch only changes provided fields; others remain unchanged."""
        created = self._create_task(client, auth_headers)
        resp = client.patch(
            f"{_BASE}/{created['id']}",
            json={"priority": "high"},
            headers=auth_headers,
        )
        self.assert_http(resp, 200)
        body = resp.json()
        assert body["priority"] == "high"
        assert body["title"] == _TASK_1["title"]  # unchanged

    def test_update_task_not_found(self, client: TestClient, auth_headers: dict) -> None:
        """Updating a non-existent task returns 404."""
        resp = client.patch(f"{_BASE}/99999", json={"title": "x"}, headers=auth_headers)
        self.assert_http(resp, 404)

    def test_update_task_wrong_owner(self, client: TestClient, auth_headers: dict) -> None:
        """Bob cannot update Alice's task."""
        created = self._create_task(client, auth_headers)

        client.post("/api/v1/auth/register", json=BOB)
        bob_token = client.post(
            "/api/v1/auth/login",
            data={"username": BOB["username"], "password": BOB["password"]},
        ).json()["access_token"]

        resp = client.patch(
            f"{_BASE}/{created['id']}",
            json={"title": "Stolen"},
            headers=self.bearer(bob_token),
        )
        assert resp.status_code in (403, 404)

    def test_update_task_unauthenticated(self, client: TestClient) -> None:
        """Unauthenticated request returns 401."""
        resp = client.patch(f"{_BASE}/1", json={"title": "x"})
        self.assert_http(resp, 401)

    def test_update_task_invalid_status(self, client: TestClient, auth_headers: dict) -> None:
        """Invalid status value returns 422."""
        created = self._create_task(client, auth_headers)
        resp = client.patch(
            f"{_BASE}/{created['id']}",
            json={"status": "invalid_status"},
            headers=auth_headers,
        )
        self.assert_validation_error(resp)


class TestDeleteTask(BaseIntegrationTestCase):
    """DELETE /api/v1/tasks/{task_id}"""

    def _create_task(self, client: TestClient, headers: dict) -> dict:  # type: ignore[type-arg]
        return client.post(_BASE, json=_TASK_1, headers=headers).json()

    def test_delete_task_success(self, client: TestClient, auth_headers: dict) -> None:
        """Owner can delete their task; returns 204."""
        created = self._create_task(client, auth_headers)
        resp = client.delete(f"{_BASE}/{created['id']}", headers=auth_headers)
        self.assert_http(resp, 204)
        # Confirm it's gone
        get_resp = client.get(f"{_BASE}/{created['id']}", headers=auth_headers)
        self.assert_http(get_resp, 404)

    def test_delete_task_not_found(self, client: TestClient, auth_headers: dict) -> None:
        """Deleting a non-existent task returns 404."""
        resp = client.delete(f"{_BASE}/99999", headers=auth_headers)
        self.assert_http(resp, 404)

    def test_delete_task_wrong_owner(self, client: TestClient, auth_headers: dict) -> None:
        """Bob cannot delete Alice's task."""
        created = self._create_task(client, auth_headers)

        client.post("/api/v1/auth/register", json=BOB)
        bob_token = client.post(
            "/api/v1/auth/login",
            data={"username": BOB["username"], "password": BOB["password"]},
        ).json()["access_token"]

        resp = client.delete(f"{_BASE}/{created['id']}", headers=self.bearer(bob_token))
        assert resp.status_code in (403, 404)

    def test_delete_task_unauthenticated(self, client: TestClient) -> None:
        """Unauthenticated request returns 401."""
        resp = client.delete(f"{_BASE}/1")
        self.assert_http(resp, 401)

    def test_delete_reduces_list_count(self, client: TestClient, auth_headers: dict) -> None:
        """After deletion the task count decreases by one."""
        self._create_task(client, auth_headers)
        created2 = self._create_task(client, auth_headers)

        before = client.get(_BASE, headers=auth_headers).json()["total"]
        client.delete(f"{_BASE}/{created2['id']}", headers=auth_headers)
        after = client.get(_BASE, headers=auth_headers).json()["total"]

        assert after == before - 1


class TestTaskStats(BaseIntegrationTestCase):
    """GET /api/v1/tasks/stats"""

    _STATS = f"{_BASE}/stats"

    def test_stats_empty(self, client: TestClient, auth_headers: dict) -> None:
        """Stats for a user with no tasks are all zeros."""
        resp = client.get(self._STATS, headers=auth_headers)
        self.assert_http(resp, 200)
        body = resp.json()
        assert body["total"] == 0
        assert body["overdue"] == 0

    def test_stats_counts_by_status(self, client: TestClient, auth_headers: dict) -> None:
        """Stats reflect the correct per-status counts."""
        client.post(_BASE, json={**_TASK_1, "status": "todo"}, headers=auth_headers)
        client.post(_BASE, json={**_TASK_1, "status": "todo"}, headers=auth_headers)
        client.post(_BASE, json={**_TASK_2, "status": "in_progress"}, headers=auth_headers)
        resp = client.get(self._STATS, headers=auth_headers)
        self.assert_http(resp, 200)
        body = resp.json()
        assert body["total"] == 3
        assert body["todo"] == 2
        assert body["in_progress"] == 1
        assert body["done"] == 0

    def test_stats_unauthenticated(self, client: TestClient) -> None:
        """Unauthenticated request returns 401."""
        resp = client.get(self._STATS)
        self.assert_http(resp, 401)

    def test_stats_scoped_to_owner(self, client: TestClient, auth_headers: dict) -> None:
        """Stats only count the current user's tasks, not other users'."""
        # Alice creates tasks
        client.post(_BASE, json=_TASK_1, headers=auth_headers)

        # Bob registers and creates his own task
        client.post("/api/v1/auth/register", json=BOB)
        bob_token = client.post(
            "/api/v1/auth/login",
            data={"username": BOB["username"], "password": BOB["password"]},
        ).json()["access_token"]
        bob_headers = self.bearer(bob_token)
        client.post(_BASE, json=_TASK_2, headers=bob_headers)

        # Alice's stats should only count her 1 task
        alice_stats = client.get(self._STATS, headers=auth_headers).json()
        assert alice_stats["total"] == 1

        # Bob's stats should only count his 1 task
        bob_stats = client.get(self._STATS, headers=bob_headers).json()
        assert bob_stats["total"] == 1
