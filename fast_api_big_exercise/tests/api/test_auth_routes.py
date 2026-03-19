"""Integration tests for /api/v1/auth/* endpoints."""

from fastapi.testclient import TestClient

from tests.base import BaseIntegrationTestCase
from tests.fixtures import ALICE, BOB


class TestRegisterEndpoint(BaseIntegrationTestCase):
    """POST /api/v1/auth/register"""

    def test_register_success(self, client: TestClient) -> None:
        """Registering a new user returns 201 with the user profile."""
        resp = client.post("/api/v1/auth/register", json=ALICE)
        self.assert_http(resp, 201)
        body = resp.json()
        assert body["username"] == ALICE["username"]
        assert body["email"] == ALICE["email"]
        assert body["full_name"] == ALICE["full_name"]
        assert body["is_active"] is True
        assert "id" in body
        assert "created_at" in body
        # Password must never be returned
        assert "password" not in body
        assert "hashed_password" not in body

    def test_register_without_full_name(self, client: TestClient) -> None:
        """Registering without an optional full_name still succeeds."""
        payload = {k: v for k, v in ALICE.items() if k != "full_name"}
        resp = client.post("/api/v1/auth/register", json=payload)
        self.assert_http(resp, 201)
        assert resp.json()["full_name"] is None

    def test_register_duplicate_username(self, client: TestClient, registered_user: dict) -> None:
        """A second registration with the same username returns 409."""
        duplicate = {**ALICE, "email": "other@example.com"}
        resp = client.post("/api/v1/auth/register", json=duplicate)
        self.assert_http(resp, 409)
        assert "Username already registered" in resp.json()["detail"]

    def test_register_duplicate_email(self, client: TestClient, registered_user: dict) -> None:
        """A second registration with the same email returns 409."""
        duplicate = {**ALICE, "username": "otheralice"}
        resp = client.post("/api/v1/auth/register", json=duplicate)
        self.assert_http(resp, 409)
        assert "Email already registered" in resp.json()["detail"]

    def test_register_invalid_email(self, client: TestClient) -> None:
        """An invalid email address returns 422."""
        resp = client.post("/api/v1/auth/register", json={**ALICE, "email": "not-an-email"})
        self.assert_validation_error(resp)

    def test_register_short_username(self, client: TestClient) -> None:
        """A username shorter than 3 characters returns 422."""
        resp = client.post("/api/v1/auth/register", json={**ALICE, "username": "ab"})
        self.assert_validation_error(resp, "username")

    def test_register_short_password(self, client: TestClient) -> None:
        """A password shorter than 8 characters returns 422."""
        resp = client.post("/api/v1/auth/register", json={**ALICE, "password": "short"})
        self.assert_validation_error(resp, "password")

    def test_register_missing_required_fields(self, client: TestClient) -> None:
        """Omitting required fields returns 422."""
        resp = client.post("/api/v1/auth/register", json={"username": "alice"})
        self.assert_validation_error(resp)

    def test_register_two_different_users(self, client: TestClient) -> None:
        """Two distinct users can register successfully."""
        r1 = client.post("/api/v1/auth/register", json=ALICE)
        r2 = client.post("/api/v1/auth/register", json=BOB)
        self.assert_http(r1, 201)
        self.assert_http(r2, 201)
        assert r1.json()["id"] != r2.json()["id"]


class TestLoginEndpoint(BaseIntegrationTestCase):
    """POST /api/v1/auth/login"""

    def test_login_success(self, client: TestClient, registered_user: dict) -> None:
        """Correct credentials return a JWT access token."""
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": ALICE["username"], "password": ALICE["password"]},
        )
        self.assert_http(resp, 200)
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 0

    def test_login_wrong_password(self, client: TestClient, registered_user: dict) -> None:
        """Wrong password returns 401."""
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": ALICE["username"], "password": "wrongpassword"},
        )
        self.assert_http(resp, 401)

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        """Unknown username returns 401."""
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "ghost", "password": "password123"},
        )
        self.assert_http(resp, 401)

    def test_login_missing_username(self, client: TestClient) -> None:
        """Missing username field returns 422."""
        resp = client.post("/api/v1/auth/login", data={"password": "password123"})
        self.assert_validation_error(resp)

    def test_login_missing_password(self, client: TestClient) -> None:
        """Missing password field returns 422."""
        resp = client.post("/api/v1/auth/login", data={"username": ALICE["username"]})
        self.assert_validation_error(resp)

    def test_login_returns_different_tokens_for_different_users(self, client: TestClient) -> None:
        """Different users get different tokens."""
        client.post("/api/v1/auth/register", json=ALICE)
        client.post("/api/v1/auth/register", json=BOB)
        r1 = client.post(
            "/api/v1/auth/login",
            data={"username": ALICE["username"], "password": ALICE["password"]},
        )
        r2 = client.post(
            "/api/v1/auth/login",
            data={"username": BOB["username"], "password": BOB["password"]},
        )
        assert r1.json()["access_token"] != r2.json()["access_token"]


class TestGetMeEndpoint(BaseIntegrationTestCase):
    """GET /api/v1/auth/me"""

    def test_get_me_success(self, client: TestClient, auth_headers: dict) -> None:
        """Authenticated request returns the current user's profile."""
        resp = client.get("/api/v1/auth/me", headers=auth_headers)
        self.assert_http(resp, 200)
        body = resp.json()
        assert body["username"] == ALICE["username"]
        assert body["email"] == ALICE["email"]
        assert body["is_active"] is True

    def test_get_me_unauthenticated(self, client: TestClient) -> None:
        """Request without a token returns 401."""
        resp = client.get("/api/v1/auth/me")
        self.assert_http(resp, 401)

    def test_get_me_invalid_token(self, client: TestClient) -> None:
        """Request with a bogus token returns 401."""
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.not.valid"},
        )
        self.assert_http(resp, 401)

    def test_get_me_malformed_authorization_header(self, client: TestClient) -> None:
        """Missing 'Bearer' prefix returns 401."""
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "NotBearer sometoken"},
        )
        self.assert_http(resp, 401)
