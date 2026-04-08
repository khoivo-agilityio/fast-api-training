# API Changelog

## [0.1.0] — 2026-03-31

### Added

#### Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Create a new user account. Triggers simulated welcome email.
- `POST /api/v1/auth/login` — Exchange credentials for JWT access + refresh tokens.
- `POST /api/v1/auth/refresh` — Rotate access token using a valid refresh token.

#### Users (`/api/v1/users`)
- `GET /api/v1/users/me` — Return the currently authenticated user's profile.
- `PATCH /api/v1/users/me` — Update display name, email, or password.

#### Projects (`/api/v1/projects`)
- `POST /api/v1/projects` — Create a new project. Owner is automatically added as Admin member. Triggers simulated project-created email.
- `GET /api/v1/projects` — List all projects the requester is a member of.
- `GET /api/v1/projects/{project_id}` — Retrieve a single project by ID.
- `PATCH /api/v1/projects/{project_id}` — Update project name / description (Admin / Manager only).
- `DELETE /api/v1/projects/{project_id}` — Delete a project (Admin only).
- `POST /api/v1/projects/{project_id}/members` — Add a user to the project (Admin / Manager only).
- `GET /api/v1/projects/{project_id}/members` — List all project members.
- `PATCH /api/v1/projects/{project_id}/members/{user_id}` — Change a member's role (Admin only).
- `DELETE /api/v1/projects/{project_id}/members/{user_id}` — Remove a member (Admin only).

#### Tasks (`/api/v1/projects/{project_id}/tasks`)
- `POST /api/v1/projects/{project_id}/tasks` — Create a task. Triggers simulated assignment email if `assignee_id` is set.
- `GET /api/v1/projects/{project_id}/tasks` — List tasks with optional filtering (`status`, `assignee_id`, `priority`), sorting (`created_at`, `due_date`, `priority`, `title`), and pagination (`limit`, `offset`).
- `GET /api/v1/projects/{project_id}/tasks/{task_id}` — Retrieve a single task.
- `PATCH /api/v1/projects/{project_id}/tasks/{task_id}` — Update task fields. Triggers:
  - Simulated email if `assignee_id` changes.
  - WebSocket notification to the assignee if `status` changes.
- `DELETE /api/v1/projects/{project_id}/tasks/{task_id}` — Delete a task (creator or Admin/Manager).

#### Comments (`/api/v1/projects/{project_id}/tasks/{task_id}/comments`)
- `POST /api/v1/projects/{project_id}/tasks/{task_id}/comments` — Add a comment to a task.
- `GET /api/v1/projects/{project_id}/tasks/{task_id}/comments` — List all comments on a task.
- `PATCH /api/v1/projects/{project_id}/tasks/{task_id}/comments/{comment_id}` — Edit a comment (author only).
- `DELETE /api/v1/projects/{project_id}/tasks/{task_id}/comments/{comment_id}` — Delete a comment (author or Admin).

#### WebSocket (`/ws`)
- `GET /ws/notifications?token={access_jwt}` — Open a persistent WebSocket connection. Receives real-time JSON push when a task assigned to the user changes status.

  Message format:
  ```json
  {
    "type": "task_status_changed",
    "task_id": 7,
    "task_title": "Implement login page",
    "new_status": "in_progress",
    "project_id": 3
  }
  ```

#### Health
- `GET /health` — Returns `{"status": "healthy", "version": "0.1.0"}`.

---

### Infrastructure & Cross-cutting

| Feature | Details |
|---------|---------|
| **RBAC** | Role-based permissions: `admin` > `manager` > `member`. Enforced per-endpoint. |
| **Background tasks** | FastAPI `BackgroundTasks` — simulated emails logged via `structlog`. |
| **WebSocket manager** | `ConnectionManager` singleton; supports multiple connections per user. |
| **Middleware** | Per-request UUID (`X-Request-ID`), execution timing headers, structured JSON logs. |
| **CORS** | Configured for `http://localhost:3000`. |
| **Swagger** | Available at `/docs` (Swagger UI) and `/redoc` (ReDoc). |

---

### Upgrade Notes

_Initial release — no migration from a previous version._
