import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_logout_endpoint(client, auth_headers):
    response = await client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"detail": "Successfully logged out"}
