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


class TestUserListing:
    LIST_URL = "/api/v1/users"

    async def test_authenticated_can_list_users(
        self, client, auth_headers, create_test_user
    ):
        # create an extra regular user
        await create_test_user(username="extra", email="extra@example.com")
        resp = await client.get(self.LIST_URL, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 2
        for u in data["items"]:
            assert "hashed_password" not in u

    async def test_unauthenticated_cannot_list_users(self, client):
        resp = await client.get(self.LIST_URL)
        assert resp.status_code in (401, 403)

    async def test_list_pagination(self, client, auth_headers, create_test_user):
        # Create 4 extra users (auth_headers user already exists = 5 total)
        for i in range(4):
            await create_test_user(username=f"user{i}", email=f"user{i}@example.com")
        r1 = await client.get(f"{self.LIST_URL}?limit=2&offset=0", headers=auth_headers)
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["total"] == 5
        assert len(d1["items"]) == 2
        assert d1["limit"] == 2
        assert d1["offset"] == 0

        r2 = await client.get(f"{self.LIST_URL}?limit=2&offset=2", headers=auth_headers)
        d2 = r2.json()
        assert len(d2["items"]) == 2

        r3 = await client.get(f"{self.LIST_URL}?limit=2&offset=4", headers=auth_headers)
        d3 = r3.json()
        assert len(d3["items"]) == 1
