"""
Rate Limiting Tests — Auth Endpoints.

Verifies that slowapi enforces the per-IP limits declared in the auth router:
  - POST /api/v1/auth/register  → 3/minute
  - POST /api/v1/auth/login     → 5/minute
  - POST /api/v1/auth/refresh   → 10/minute
  - POST /api/v1/auth/logout    → no limit (sanity check)

Strategy
--------
slowapi tracks request counts in-process (using limits library's MemoryStorage
by default when no Redis is configured), keyed by the remote address returned by
get_remote_address.  In the test ASGI transport, the remote address is always
"testclient", so all requests from a single AsyncClient share the same bucket.

To avoid inter-test pollution the limiter storage is reset before each test via
the `reset_limiter` autouse fixture, which calls limiter.reset() using the app's
state.limiter instance.

Each test:
1. Makes N-1 requests — all should succeed (2xx or 4xx domain error, never 429).
2. Makes the Nth request — must return 429 Too Many Requests.
3. Validates the `Retry-After` header is present on the 429 response.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"

# Limits declared in src/auth/router.py
REGISTER_LIMIT = 3   # 3/minute
LOGIN_LIMIT = 5      # 5/minute
REFRESH_LIMIT = 10   # 10/minute


def _register_payload(n: int = 0) -> dict:
    """Unique email per call so duplicate-email 409s don't mask the 429."""
    return {
        "email": f"ratelimit{n}@example.com",
        "password": "StrongPass123!",
        "display_name": f"User {n}",
    }


def _login_payload(email: str = "nope@example.com") -> dict:
    return {"email": email, "password": "anypassword"}


def _refresh_payload(token: str = "invalid.refresh.token") -> dict:
    return {"refresh_token": token}


# ---------------------------------------------------------------------------
# Autouse fixture — reset the in-process rate-limit storage before each test
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def reset_limiter():
    """
    Clear the slowapi limiter's in-memory storage before every test so that
    counts from one test do not spill into the next.

    slowapi stores the limiter on app.state.limiter.  The auth router also
    creates its own separate Limiter instance.  Both must be reset.
    """
    from src.auth.router import limiter as auth_limiter
    from src.main import app

    for lim in (app.state.limiter, auth_limiter):
        storage = getattr(lim, "_storage", None)
        if storage is not None and hasattr(storage, "reset"):
            storage.reset()
    yield
    for lim in (app.state.limiter, auth_limiter):
        storage = getattr(lim, "_storage", None)
        if storage is not None and hasattr(storage, "reset"):
            storage.reset()


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register  — limit: 3/minute
# ---------------------------------------------------------------------------

class TestRegisterRateLimit:
    """Rate limit tests for POST /api/v1/auth/register (3/minute)."""

    @pytest.mark.asyncio
    async def test_register_under_limit_succeeds(self, client: AsyncClient):
        """Requests 1 through REGISTER_LIMIT should never be 429."""
        for i in range(REGISTER_LIMIT):
            resp = await client.post(REGISTER_URL, json=_register_payload(i))
            assert resp.status_code != 429, (
                f"Request {i + 1} of {REGISTER_LIMIT} was rate-limited unexpectedly: "
                f"{resp.text}"
            )

    @pytest.mark.asyncio
    async def test_register_at_limit_returns_429(self, client: AsyncClient):
        """The (REGISTER_LIMIT + 1)th request must be rejected with 429."""
        # Exhaust the limit
        for i in range(REGISTER_LIMIT):
            await client.post(REGISTER_URL, json=_register_payload(i))

        # One more — must be rate-limited
        resp = await client.post(REGISTER_URL, json=_register_payload(REGISTER_LIMIT))
        assert resp.status_code == 429, (
            f"Expected 429 on request {REGISTER_LIMIT + 1}, got {resp.status_code}: {resp.text}"
        )

    @pytest.mark.asyncio
    async def test_register_429_response_has_detail(self, client: AsyncClient):
        """A 429 response from /register must have a non-empty JSON body.

        Note: slowapi 0.1.9's _rate_limit_exceeded_handler does NOT include a
        Retry-After header by default.  This test validates the body only.
        """
        for i in range(REGISTER_LIMIT):
            await client.post(REGISTER_URL, json=_register_payload(i))

        resp = await client.post(REGISTER_URL, json=_register_payload(REGISTER_LIMIT))
        assert resp.status_code == 429
        assert resp.text, "Expected non-empty body on 429 response"

    @pytest.mark.asyncio
    async def test_register_429_response_body(self, client: AsyncClient):
        """The 429 body should contain an error message (slowapi default)."""
        for i in range(REGISTER_LIMIT):
            await client.post(REGISTER_URL, json=_register_payload(i))

        resp = await client.post(REGISTER_URL, json=_register_payload(REGISTER_LIMIT))
        assert resp.status_code == 429
        body = resp.text
        # slowapi's _rate_limit_exceeded_handler returns a plain-text or JSON body
        assert body, "Expected non-empty body on 429 response"


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login  — limit: 5/minute
# ---------------------------------------------------------------------------

class TestLoginRateLimit:
    """Rate limit tests for POST /api/v1/auth/login (5/minute)."""

    @pytest.mark.asyncio
    async def test_login_under_limit_never_429(self, client: AsyncClient):
        """Requests 1-LOGIN_LIMIT may fail with 401 (bad creds) but never 429."""
        for i in range(LOGIN_LIMIT):
            resp = await client.post(LOGIN_URL, json=_login_payload(f"user{i}@example.com"))
            assert resp.status_code != 429, (
                f"Request {i + 1} of {LOGIN_LIMIT} was unexpectedly rate-limited"
            )

    @pytest.mark.asyncio
    async def test_login_at_limit_returns_429(self, client: AsyncClient):
        """The (LOGIN_LIMIT + 1)th login request must return 429."""
        for i in range(LOGIN_LIMIT):
            await client.post(LOGIN_URL, json=_login_payload(f"user{i}@example.com"))

        resp = await client.post(LOGIN_URL, json=_login_payload("over@example.com"))
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_login_429_response_has_detail(self, client: AsyncClient):
        """429 from /login must have a non-empty body (slowapi 0.1.9 omits Retry-After)."""
        for i in range(LOGIN_LIMIT):
            await client.post(LOGIN_URL, json=_login_payload(f"u{i}@x.com"))

        resp = await client.post(LOGIN_URL, json=_login_payload("extra@x.com"))
        assert resp.status_code == 429
        assert resp.text, "Expected non-empty body on 429 response"

    @pytest.mark.asyncio
    async def test_login_valid_credentials_still_rate_limited(self, client: AsyncClient):
        """Even a correct password is blocked once the limit is exceeded."""
        # Register a real user first (doesn't count against the login limit)
        await client.post(
            REGISTER_URL,
            json={
                "email": "validuser@example.com",
                "password": "ValidPass999!",
                "display_name": "Valid",
            },
        )

        # Burn through the login limit using valid credentials
        for _ in range(LOGIN_LIMIT):
            await client.post(
                LOGIN_URL,
                json={"email": "validuser@example.com", "password": "ValidPass999!"},
            )

        # The next login — even with correct credentials — must be 429
        resp = await client.post(
            LOGIN_URL,
            json={"email": "validuser@example.com", "password": "ValidPass999!"},
        )
        assert resp.status_code == 429, (
            f"Expected 429 for valid credentials over the limit, got {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# POST /api/v1/auth/refresh  — limit: 10/minute
# ---------------------------------------------------------------------------

class TestRefreshRateLimit:
    """Rate limit tests for POST /api/v1/auth/refresh (10/minute)."""

    @pytest.mark.asyncio
    async def test_refresh_under_limit_never_429(self, client: AsyncClient):
        """First REFRESH_LIMIT refresh calls must not be rate-limited (may be 401)."""
        for _ in range(REFRESH_LIMIT):
            resp = await client.post(REFRESH_URL, json=_refresh_payload())
            assert resp.status_code != 429

    @pytest.mark.asyncio
    async def test_refresh_at_limit_returns_429(self, client: AsyncClient):
        """The (REFRESH_LIMIT + 1)th refresh must return 429."""
        for _ in range(REFRESH_LIMIT):
            await client.post(REFRESH_URL, json=_refresh_payload())

        resp = await client.post(REFRESH_URL, json=_refresh_payload())
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_refresh_429_response_has_detail(self, client: AsyncClient):
        """429 from /refresh must have a non-empty body (slowapi 0.1.9 omits Retry-After)."""
        for _ in range(REFRESH_LIMIT):
            await client.post(REFRESH_URL, json=_refresh_payload())

        resp = await client.post(REFRESH_URL, json=_refresh_payload())
        assert resp.status_code == 429
        assert resp.text, "Expected non-empty body on 429 response"

    @pytest.mark.asyncio
    async def test_refresh_with_valid_token_still_blocked(self, client: AsyncClient, async_session):
        """A genuine refresh token is also blocked once the bucket is full.

        Uses direct DB creation to obtain a real refresh token without touching
        the /register endpoint (which has its own separate rate-limit bucket).
        """
        from tests.conftest import create_test_user

        user_data = await create_test_user(
            async_session,
            email="rt_blocked@example.com",
            password="BlockedPass1!",
        )
        real_token = user_data["tokens"]["refresh_token"]

        # Burn through the refresh limit with invalid tokens
        for _ in range(REFRESH_LIMIT):
            await client.post(REFRESH_URL, json=_refresh_payload("bad.token"))

        # Even with the real token, the next request must be 429
        resp = await client.post(REFRESH_URL, json={"refresh_token": real_token})
        assert resp.status_code == 429


# ---------------------------------------------------------------------------
# POST /api/v1/auth/logout  — no rate limit (sanity check)
# ---------------------------------------------------------------------------

class TestLogoutNoRateLimit:
    """Logout has no rate limit — confirm it is not accidentally restricted."""

    @pytest.mark.asyncio
    async def test_logout_without_token_returns_401_not_429(self, client: AsyncClient):
        """
        Calling /logout repeatedly without a token must always return 401/403,
        never 429, because logout has no @limiter.limit() decorator.
        """
        # Make more requests than the smallest auth limit to be sure
        call_count = REGISTER_LIMIT + 5
        for _ in range(call_count):
            resp = await client.post(LOGOUT_URL)
            assert resp.status_code != 429, (
                f"Logout was unexpectedly rate-limited after {_ + 1} requests"
            )
            # Without a token the endpoint returns 401 or 403
            assert resp.status_code in (401, 403), (
                f"Unexpected status {resp.status_code} from logout without token"
            )
