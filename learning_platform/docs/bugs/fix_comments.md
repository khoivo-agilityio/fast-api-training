# Overview
    - This document note the issue with code that my supporter ask me to fix.

# Issues

1. learning_platform/src/admin/__init__.py  0 → 100644
   - Maintainer: Vu Phan
   - `What's the admin module? Can you explain the purpose of this module to me?`

2. learning_platform/src/auth/security.py  0 → 100644

passlib's bcrypt wrapper is incompatible with bcrypt >= 4.1.
Using bcrypt directly avoids this issue.
"""

import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
Comment on lines +10 to +17
    - Comment: `Should apply async to these functions?`

3. learning_platform/src/auth/service.py  0 → 100644
    - Comment: `Should create a class and add all service functions to it?`

4. learning_platform/src/users/service.py  0 → 100644
    - Comment: `Should create a class for service?`

5. learning_platform/tests/users/test_users.py  0 → 100644
    """PATCH /api/v1/users/me"""

    async def test_update_display_name(self, client: AsyncClient, auth_headers):
        resp = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"display_name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated Name"

    async def test_update_avatar(self, client: AsyncClient, auth_headers):
        resp = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"avatar": "https://example.com/avatar.png"},
    - Comment: `can you research how to store media files on the server?`

