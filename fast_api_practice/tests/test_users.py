class TestUserRoutes:
    ME_URL = "/api/v1/users/me"

    async def test_get_me_success(self, client, auth_headers):
        resp = await client.get(self.ME_URL, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert "hashed_password" not in data

    async def test_get_me_no_token(self, client):
        resp = await client.get(self.ME_URL)
        assert resp.status_code in (401, 403)

    async def test_get_me_invalid_token(self, client):
        resp = await client.get(
            self.ME_URL, headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert resp.status_code == 401

    async def test_update_me_full_name(self, client, auth_headers):
        resp = await client.patch(
            self.ME_URL,
            headers=auth_headers,
            json={"full_name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Updated Name"

    async def test_update_me_email(self, client, auth_headers):
        resp = await client.patch(
            self.ME_URL,
            headers=auth_headers,
            json={"email": "newemail@example.com"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "newemail@example.com"

    async def test_update_me_no_fields(self, client, auth_headers):
        resp = await client.patch(
            self.ME_URL,
            headers=auth_headers,
            json={},
        )
        assert resp.status_code == 400
