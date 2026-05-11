# API Changelog

## v0.1.0 — 2026-05-04

### Added

#### Auth (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Register new user (role defaults to student)
- `POST /api/v1/auth/login` — Login, returns access + refresh tokens
- `POST /api/v1/auth/refresh` — Rotate tokens (blacklist old refresh, issue new pair)
- `POST /api/v1/auth/logout` — Blacklist current access token in Redis

#### Users (`/api/v1/users`)
- `GET /api/v1/users/me` — Get current user profile
- `PATCH /api/v1/users/me` — Update current user profile (display_name, avatar, password)

#### System
- `GET /health` — Health check

### Changed (Code Review Fixes)

| # | File | Review Comment | Resolution |
|---|------|---------------|------------|
| 1 | `src/admin/__init__.py` | "What's the admin module?" | Added comprehensive module docstring + `README.md` |
| 2 | `src/auth/security.py` | "Should apply async?" | Made `hash_password`/`verify_password` async with `run_in_executor` |
| 3 | `src/auth/service.py` | "Should create a class?" | Refactored to class-based `AuthService` |
| 4 | `src/users/service.py` | "Should create a class?" | Refactored to class-based `UserService` |
| 5 | `tests/users/test_users.py` | "Research media file storage?" | Documented recommendations in this changelog (see below) |

### Media File Storage Research (Issue #5)

The reviewer asked: *"Can you research how to store media files on the server?"*

**Recommendation for this project:**

| Approach | When to Use | Implementation |
|----------|-------------|----------------|
| **URL-only (current)** | MVP / v1 | Store `avatar` as a URL string. User provides a link to an externally-hosted image. No server-side upload needed. |
| **Cloud Storage (S3/GCS)** | Production | Use presigned URLs. Client uploads directly to S3; server stores the object key. Best for scalability. |
| **Local file storage** | Development only | Save to a `media/` directory using `aiofiles`. Not suitable for Railway/Docker (ephemeral filesystem). |

**If implementing cloud storage in a future phase:**
1. Add `boto3` (or `aioboto3`) to dependencies
2. Create `src/storage/` module with `upload_file()` and `get_presigned_url()`
3. Add `PATCH /users/me/avatar` endpoint accepting `UploadFile`
4. Validate file type by magic bytes (not Content-Type header) using `python-magic`
5. Generate UUID filenames to prevent path traversal
6. Store the S3 object key in `users.avatar`, serve via CloudFront/CDN

**For now**: The `avatar` field stores a URL string. No server-side file upload is implemented in v0.1.0.
