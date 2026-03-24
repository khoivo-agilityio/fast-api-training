from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.domain.entities.user import UserRole
from src.infrastructure.database.repositories import SQLAlchemyUserRepository


# ── Security unit tests ──────────────────────────────────────────────────────
class TestSecurity:
    def test_hash_and_verify_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed)
        assert not verify_password("wrongpassword", hashed)

    def test_access_token_roundtrip(self):
        token = create_access_token(user_id=42, role="admin")
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"

    def test_refresh_token_roundtrip(self):
        token = create_refresh_token(user_id=42)
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == "refresh"


# ── User repository unit tests ───────────────────────────────────────────────
class TestUserRepository:
    async def test_create_user(self, db_session):
        repo = SQLAlchemyUserRepository(db_session)
        user = await repo.create(
            username="alice",
            email="alice@example.com",
            hashed_password="hashed",
        )
        assert user.id is not None
        assert user.username == "alice"
        assert user.role == UserRole.MEMBER

    async def test_get_by_username(self, db_session):
        repo = SQLAlchemyUserRepository(db_session)
        await repo.create(username="bob", email="bob@example.com", hashed_password="h")
        found = await repo.get_by_username("bob")
        assert found is not None
        assert found.username == "bob"

    async def test_get_by_username_not_found(self, db_session):
        repo = SQLAlchemyUserRepository(db_session)
        found = await repo.get_by_username("nonexistent")
        assert found is None

    async def test_get_by_email(self, db_session):
        repo = SQLAlchemyUserRepository(db_session)
        await repo.create(
            username="carol", email="carol@example.com", hashed_password="h"
        )
        found = await repo.get_by_email("carol@example.com")
        assert found is not None

    async def test_update_user(self, db_session):
        repo = SQLAlchemyUserRepository(db_session)
        user = await repo.create(
            username="dave", email="dave@example.com", hashed_password="h"
        )
        updated = await repo.update(user.id, full_name="Dave Smith")
        assert updated is not None
        assert updated.full_name == "Dave Smith"

    async def test_update_nonexistent_user(self, db_session):
        repo = SQLAlchemyUserRepository(db_session)
        result = await repo.update(9999, full_name="Ghost")
        assert result is None


# ── Auth route integration tests ─────────────────────────────────────────────
class TestAuthRoutes:
    REGISTER_URL = "/api/v1/auth/register"
    LOGIN_URL = "/api/v1/auth/login"
    REFRESH_URL = "/api/v1/auth/refresh"

    async def test_register_success(self, client):
        resp = await client.post(
            self.REGISTER_URL,
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert "hashed_password" not in data

    async def test_register_duplicate_username(self, client):
        payload = {
            "username": "dupuser",
            "email": "dup@example.com",
            "password": "password123",
        }
        await client.post(self.REGISTER_URL, json=payload)
        resp = await client.post(
            self.REGISTER_URL, json={**payload, "email": "other@example.com"}
        )
        assert resp.status_code == 409

    async def test_register_short_password(self, client):
        resp = await client.post(
            self.REGISTER_URL,
            json={
                "username": "user1",
                "email": "u1@example.com",
                "password": "short",
            },
        )
        assert resp.status_code == 422  # Pydantic validation error

    async def test_login_success(self, client):
        await client.post(
            self.REGISTER_URL,
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "password123",
            },
        )
        resp = await client.post(
            self.LOGIN_URL,
            data={"username": "loginuser", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client):
        await client.post(
            self.REGISTER_URL,
            json={
                "username": "user2",
                "email": "u2@example.com",
                "password": "password123",
            },
        )
        resp = await client.post(
            self.LOGIN_URL,
            data={"username": "user2", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client):
        resp = await client.post(
            self.LOGIN_URL,
            data={"username": "ghost", "password": "password123"},
        )
        assert resp.status_code == 401

    async def test_refresh_success(self, client):
        await client.post(
            self.REGISTER_URL,
            json={
                "username": "refreshuser",
                "email": "refresh@example.com",
                "password": "password123",
            },
        )
        login_resp = await client.post(
            self.LOGIN_URL,
            data={"username": "refreshuser", "password": "password123"},
        )
        refresh_token = login_resp.json()["refresh_token"]
        resp = await client.post(
            self.REFRESH_URL, json={"refresh_token": refresh_token}
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_with_access_token_fails(self, client):
        await client.post(
            self.REGISTER_URL,
            json={
                "username": "user3",
                "email": "u3@example.com",
                "password": "password123",
            },
        )
        login_resp = await client.post(
            self.LOGIN_URL,
            data={"username": "user3", "password": "password123"},
        )
        access_token = login_resp.json()["access_token"]
        resp = await client.post(self.REFRESH_URL, json={"refresh_token": access_token})
        assert resp.status_code == 401

    async def test_refresh_with_invalid_token(self, client):
        resp = await client.post(
            self.REFRESH_URL, json={"refresh_token": "not.a.valid.token"}
        )
        assert resp.status_code == 401
