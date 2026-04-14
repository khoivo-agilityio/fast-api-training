"""Tests for the /health endpoint."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_engine_mock(*, fail: bool = False) -> MagicMock:
    """Return a mock async_engine whose .connect() context manager either
    executes SELECT 1 successfully or raises an exception."""
    mock_conn = AsyncMock()
    if fail:
        mock_conn.execute.side_effect = Exception("DB unreachable")

    @asynccontextmanager
    async def _connect():
        yield mock_conn

    engine = MagicMock()
    engine.connect = _connect
    return engine


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    """Tests for GET /health."""

    async def test_health_returns_200(self, client: AsyncClient) -> None:
        engine = _make_engine_mock()
        with patch("src.infrastructure.database.connection.async_engine", engine):
            response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_when_db_connected(self, client: AsyncClient) -> None:
        engine = _make_engine_mock(fail=False)
        with patch("src.infrastructure.database.connection.async_engine", engine):
            response = await client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    async def test_health_when_db_disconnected(self, client: AsyncClient) -> None:
        engine = _make_engine_mock(fail=True)
        with patch("src.infrastructure.database.connection.async_engine", engine):
            response = await client.get("/health")
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "disconnected"

    async def test_health_response_has_required_fields(
        self, client: AsyncClient
    ) -> None:
        engine = _make_engine_mock()
        with patch("src.infrastructure.database.connection.async_engine", engine):
            response = await client.get("/health")
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "database" in data

    async def test_health_version_is_string(self, client: AsyncClient) -> None:
        engine = _make_engine_mock()
        with patch("src.infrastructure.database.connection.async_engine", engine):
            response = await client.get("/health")
        data = response.json()
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    @pytest.mark.parametrize("method", ["post", "put", "delete", "patch"])
    async def test_health_only_accepts_get(
        self, client: AsyncClient, method: str
    ) -> None:
        response = await getattr(client, method)("/health")
        assert response.status_code == 405
