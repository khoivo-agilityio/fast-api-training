"""Base test case classes for reusability across the test suite.

Hierarchy:
    BaseTestCase
        ├── BaseUnitTestCase        — unit tests with mock repos
        └── BaseIntegrationTestCase — integration tests with TestClient

Usage:

    # Unit test
    class TestMyService(BaseUnitTestCase):
        def test_something(self) -> None:
            service = AuthService(user_repository=self.mock_user_repo)
            ...

    # Integration test
    class TestMyRoute(BaseIntegrationTestCase):
        def test_endpoint(self) -> None:
            resp = self.client.get("/health")
            assert resp.status_code == 200
"""

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from tests.fixtures import (
    ALICE,
    BOB,
    make_task,
    make_user,
)


class BaseTestCase:
    """Root base class shared by all test cases.

    Provides:
    - Common assertion helpers
    - Access to entity builders (``make_user``, ``make_task``)
    - Constants (``ALICE``, ``BOB``)
    """

    # ── Entity builders available as class-level shortcuts ────────────────
    make_user = staticmethod(make_user)
    make_task = staticmethod(make_task)

    # ── Shared test-user constants ────────────────────────────────────────
    ALICE = ALICE
    BOB = BOB

    # ── Common assertions ─────────────────────────────────────────────────
    def assert_http(self, response, expected_status: int) -> None:  # type: ignore[no-untyped-def]
        """Assert HTTP status code with a clear failure message."""
        assert (
            response.status_code == expected_status
        ), f"Expected HTTP {expected_status}, got {response.status_code}.\nBody: {response.text}"

    def assert_validation_error(self, response, field: str | None = None) -> None:  # type: ignore[no-untyped-def]
        """Assert a 422 Unprocessable Entity with an optional field check."""
        self.assert_http(response, 422)
        if field:
            assert (
                field in response.text
            ), f"Expected field '{field}' in validation error. Got: {response.text}"


# ============================================================================
# UNIT TEST BASE
# ============================================================================


class BaseUnitTestCase(BaseTestCase):
    """Base for unit tests that use mock repositories (no DB, no HTTP).

    Fixtures ``mock_user_repo``, ``mock_task_repo``, ``auth_service``, and
    ``task_service`` are injected by pytest through ``conftest.py`` — subclasses
    declare them as method parameters in the normal pytest style.

    Example::

        class TestRegister(BaseUnitTestCase):
            def test_success(
                self,
                auth_service: AuthService,
                mock_user_repo: MagicMock,
            ) -> None:
                ...
    """

    @staticmethod
    def make_mock_repo() -> MagicMock:
        """Return a plain MagicMock useful as a one-off repository stub."""
        return MagicMock()


# ============================================================================
# INTEGRATION TEST BASE
# ============================================================================


class BaseIntegrationTestCase(BaseTestCase):
    """Base for integration tests that send HTTP requests via TestClient.

    The ``client``, ``registered_user``, ``auth_token``, and ``auth_headers``
    fixtures are injected by pytest through ``conftest.py``.

    Example::

        class TestHealthCheck(BaseIntegrationTestCase):
            def test_health(self, client: TestClient) -> None:
                resp = client.get("/health")
                self.assert_http(resp, 200)
                assert resp.json()["status"] == "healthy"
    """

    # ── HTTP helpers ──────────────────────────────────────────────────────

    def post_json(  # type: ignore[no-untyped-def]
        self,
        client: TestClient,
        url: str,
        payload: dict,  # type: ignore[type-arg]
        headers: dict | None = None,  # type: ignore[type-arg]
        expected_status: int = 200,
    ) -> dict:  # type: ignore[type-arg]
        """POST JSON and assert the expected status; return the parsed body."""
        resp = client.post(url, json=payload, headers=headers or {})
        self.assert_http(resp, expected_status)
        return resp.json()

    def register(  # type: ignore[no-untyped-def]
        self,
        client: TestClient,
        user: dict | None = None,  # type: ignore[type-arg]
    ) -> dict:  # type: ignore[type-arg]
        """Register a user (defaults to ALICE) and return the response body."""
        return self.post_json(
            client,
            "/api/v1/auth/register",
            user or self.ALICE,
            expected_status=201,
        )

    def login(  # type: ignore[no-untyped-def]
        self,
        client: TestClient,
        username: str = "",
        password: str = "",
    ) -> str:
        """Log in and return the JWT access-token string."""
        resp = client.post(
            "/api/v1/auth/login",
            data={
                "username": username or self.ALICE["username"],
                "password": password or self.ALICE["password"],
            },
        )
        self.assert_http(resp, 200)
        return resp.json()["access_token"]

    def bearer(self, token: str) -> dict[str, str]:
        """Wrap a token in an Authorization header dict."""
        return {"Authorization": f"Bearer {token}"}
