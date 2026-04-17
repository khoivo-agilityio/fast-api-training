# API Changelog

All notable changes to the **public API surface** are documented here.
This project follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [0.2.0] — 2026-04-14

### Changed

- **`GET /health`** — Response now includes a `database` field reporting live
  connectivity status.

  | Field | Before | After |
  |-------|--------|-------|
  | `status` | `"healthy"` only | `"healthy"` \| `"degraded"` |
  | `database` | _(absent)_ | `"connected"` \| `"disconnected"` \| `"unknown"` |

  **Before:**
  ```json
  { "status": "healthy", "version": "0.1.0" }
  ```
  **After:**
  ```json
  { "status": "healthy", "version": "0.1.0", "database": "connected" }
  ```

  When the database is unreachable `status` becomes `"degraded"` instead of
  `"healthy"`. Existing clients that only check `status == "healthy"` are
  unaffected when the DB is up; add a `database` check for deeper monitoring.

### Infrastructure (non-API surface changes)

- Added multi-stage `Dockerfile` (`python:3.14-slim`, non-root `appuser`).
- Added `docker-entrypoint.sh` — runs Alembic migrations before server start.
- Added `docker-compose.yml` — local dev stack (app + PostgreSQL 16 + Redis 7).
- Added `docker-compose.test.yml` — test runner with Dockerised PostgreSQL.
- Added `railway.toml` — Railway deployment (Dockerfile builder, `/health` check).
- Added `.github/workflows/ci.yml` — CI pipeline (lint → test → docker build).
- Fixed Alembic migration `a2235df5580e` — `ALTER TYPE ADD VALUE` now committed
  in its own transaction before DML referencing new enum values.
- Removed duplicate migration `a1b2c3d4e5f6` (stale hand-written file).

---

## [0.1.0] — 2026-03-20 (Initial Release)

### Added

- `POST /api/v1/auth/register` — User registration.
- `POST /api/v1/auth/login` — JWT login (access + refresh tokens).
- `POST /api/v1/auth/refresh` — Token refresh.
- `GET /api/v1/users/me` — Current user profile.
- `PATCH /api/v1/users/me` — Update profile.
- `GET/POST /api/v1/projects` — Project list and creation.
- `GET/PATCH/DELETE /api/v1/projects/{id}` — Project detail, update, delete.
- `POST /api/v1/projects/{id}/members` — Add project member.
- `DELETE /api/v1/projects/{id}/members/{user_id}` — Remove member.
- `GET/POST /api/v1/projects/{id}/tasks` — Task list and creation.
- `GET/PATCH/DELETE /api/v1/tasks/{id}` — Task detail, update, delete.
- `GET/POST /api/v1/tasks/{id}/comments` — Comment list and creation.
- `DELETE /api/v1/comments/{id}` — Delete comment.
- `GET /health` — Basic health check.
- `GET /ws/notifications` — WebSocket real-time notifications (JWT auth).
