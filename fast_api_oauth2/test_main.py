"""
Tests for FastAPI OAuth2 authentication endpoints.

Tests cover:
- Token generation (login)
- Authentication-protected routes
- Invalid credentials
- Expired/invalid tokens
- Disabled users
"""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from main import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    app,
    create_access_token,
    fake_users_db,
    get_password_hash,
)

client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def valid_token():
    """Generate a valid access token for testing."""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "johndoe"}, expires_delta=access_token_expires
    )
    return access_token


@pytest.fixture
def expired_token():
    """Generate an expired access token for testing."""
    access_token = create_access_token(
        data={"sub": "johndoe"}, expires_delta=timedelta(minutes=-1)
    )
    return access_token


@pytest.fixture
def invalid_token():
    """Generate an invalid access token."""
    return "invalid.token.here"


@pytest.fixture
def disabled_user_token():
    """Create a token for a disabled user."""
    # Temporarily add a disabled user
    fake_users_db["disableduser"] = {
        "username": "disableduser",
        "full_name": "Disabled User",
        "email": "disabled@example.com",
        "hashed_password": get_password_hash("testpassword"),
        "disabled": True,
    }

    access_token = create_access_token(data={"sub": "disableduser"})

    yield access_token

    # Cleanup
    del fake_users_db["disableduser"]


# ============================================================================
# TEST TOKEN ENDPOINT (LOGIN)
# ============================================================================


def test_login_success():
    """Test successful login with correct credentials."""
    response = client.post(
        "/token",
        data={
            "username": "johndoe",
            "password": "secret",
        },
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"
    assert isinstance(json_response["access_token"], str)
    assert len(json_response["access_token"]) > 0


def test_login_invalid_username():
    """Test login with non-existent username."""
    response = client.post(
        "/token",
        data={
            "username": "nonexistent",
            "password": "secret",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_invalid_password():
    """Test login with incorrect password."""
    response = client.post(
        "/token",
        data={
            "username": "johndoe",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_missing_username():
    """Test login without username."""
    response = client.post(
        "/token",
        data={
            "password": "secret",
        },
    )

    assert response.status_code == 422  # Validation error


def test_login_missing_password():
    """Test login without password."""
    response = client.post(
        "/token",
        data={
            "username": "johndoe",
        },
    )

    assert response.status_code == 422  # Validation error


def test_login_empty_credentials():
    """Test login with empty credentials."""
    response = client.post(
        "/token",
        data={
            "username": "",
            "password": "",
        },
    )

    assert response.status_code == 422


# ============================================================================
# TEST /users/me/ ENDPOINT
# ============================================================================


def test_read_users_me_success(valid_token):
    """Test getting current user info with valid token."""
    response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["username"] == "johndoe"
    assert json_response["email"] == "johndoe@example.com"
    assert json_response["full_name"] == "John Doe"
    assert json_response["disabled"] is False
    # Should not include hashed_password
    assert "hashed_password" not in json_response


def test_read_users_me_no_token():
    """Test accessing /users/me/ without authentication token."""
    response = client.get("/users/me/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_read_users_me_invalid_token(invalid_token):
    """Test accessing /users/me/ with invalid token."""
    response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_read_users_me_expired_token(expired_token):
    """Test accessing /users/me/ with expired token."""
    response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_read_users_me_malformed_header(valid_token):
    """Test accessing /users/me/ with malformed Authorization header."""
    # Missing "Bearer" prefix
    response = client.get(
        "/users/me/",
        headers={"Authorization": valid_token},
    )

    assert response.status_code == 401


def test_read_users_me_disabled_user(disabled_user_token):
    """Test accessing /users/me/ with disabled user account."""
    response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {disabled_user_token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"


# ============================================================================
# TEST /users/me/items/ ENDPOINT
# ============================================================================


def test_read_own_items_success(valid_token):
    """Test getting user's own items with valid token."""
    response = client.get(
        "/users/me/items/",
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 200
    json_response = response.json()
    assert isinstance(json_response, list)
    assert len(json_response) > 0
    assert json_response[0]["item_id"] == "Foo"
    assert json_response[0]["owner"] == "johndoe"


def test_read_own_items_no_token():
    """Test accessing /users/me/items/ without authentication token."""
    response = client.get("/users/me/items/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_read_own_items_invalid_token(invalid_token):
    """Test accessing /users/me/items/ with invalid token."""
    response = client.get(
        "/users/me/items/",
        headers={"Authorization": f"Bearer {invalid_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_read_own_items_expired_token(expired_token):
    """Test accessing /users/me/items/ with expired token."""
    response = client.get(
        "/users/me/items/",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_read_own_items_disabled_user(disabled_user_token):
    """Test accessing /users/me/items/ with disabled user account."""
    response = client.get(
        "/users/me/items/",
        headers={"Authorization": f"Bearer {disabled_user_token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Inactive user"


# ============================================================================
# INTEGRATION TESTS (FULL FLOW)
# ============================================================================


def test_full_authentication_flow():
    """Test complete authentication flow: login -> access protected route."""
    # Step 1: Login to get token
    login_response = client.post(
        "/token",
        data={
            "username": "johndoe",
            "password": "secret",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Step 2: Use token to access protected route
    user_response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert user_response.status_code == 200
    assert user_response.json()["username"] == "johndoe"

    # Step 3: Access another protected route with same token
    items_response = client.get(
        "/users/me/items/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert items_response.status_code == 200
    assert len(items_response.json()) > 0


def test_token_reuse():
    """Test that the same token can be used for multiple requests."""
    # Get token
    login_response = client.post(
        "/token",
        data={"username": "johndoe", "password": "secret"},
    )
    token = login_response.json()["access_token"]

    # Use token multiple times
    for _ in range(3):
        response = client.get(
            "/users/me/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200


# ============================================================================
# SECURITY TESTS
# ============================================================================


def test_token_cannot_access_other_users():
    """Test that a user's token cannot be used to access other users' data."""
    # In this simple example, we only have one user
    # But this test demonstrates the pattern for multi-user systems

    # Get token for johndoe
    login_response = client.post(
        "/token",
        data={"username": "johndoe", "password": "secret"},
    )
    token = login_response.json()["access_token"]

    # Access user's own data (should work)
    response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "johndoe"


def test_sql_injection_in_username():
    """Test that SQL injection attempts in username are handled safely."""
    response = client.post(
        "/token",
        data={
            "username": "admin' OR '1'='1",
            "password": "anything",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_special_characters_in_credentials():
    """Test handling of special characters in credentials."""
    response = client.post(
        "/token",
        data={
            "username": "user@#$%",
            "password": "pass!@#$%^&*()",
        },
    )

    assert response.status_code == 401


# ============================================================================
# EDGE CASES
# ============================================================================


def test_very_long_username():
    """Test authentication with extremely long username."""
    long_username = "a" * 10000
    response = client.post(
        "/token",
        data={
            "username": long_username,
            "password": "secret",
        },
    )

    assert response.status_code == 401


def test_case_sensitive_username():
    """Test that username is case-sensitive."""
    response = client.post(
        "/token",
        data={
            "username": "JOHNDOE",  # Uppercase
            "password": "secret",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_whitespace_in_credentials():
    """Test handling of whitespace in credentials."""
    # Leading/trailing whitespace
    response = client.post(
        "/token",
        data={
            "username": " johndoe ",
            "password": " secret ",
        },
    )

    assert response.status_code == 401
