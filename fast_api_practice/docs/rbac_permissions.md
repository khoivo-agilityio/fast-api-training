# RBAC Permission Reference

> **Last updated:** 2026-04-06  
> Audience: developers, QA, tech-leads

---

## Role Definitions

### Project Member Roles (`ProjectMemberRole`)

Stored per-project in the `project_members` table.

| Role | String value | Description |
|---|---|---|
| **ADMIN** | `"admin"` | Full control over a project: can update/delete the project, add/remove members, change member roles, and modify any task or comment inside the project. Automatically assigned to the user who creates the project. |
| **MEMBER** | `"member"` | Can participate inside the project: create tasks, update their own tasks, and write/edit/delete their own comments. Cannot manage membership or delete the project. |

> **Note:** There is no system-wide admin role in the current model. The owner of a project is always given the `ADMIN` role in `project_members` at creation time, so ownership and the `ADMIN` role are equivalent.

---

## How RBAC Is Enforced

```
HTTP Request
    │
    ▼
FastAPI Route (src/api/v1/*.py)
    │  calls service method with requester_id
    ▼
Domain Service (src/domain/services/*.py)
    │  checks role via _require_project_admin / _require_project_member
    │  raises PermissionError on violation
    ▼
Route catches PermissionError → returns 403 Forbidden
```

RBAC logic lives **entirely in the service layer**, not in the routes. Routes only:
1. Extract `current_user` from the JWT (via `get_current_user` dependency)
2. Pass `current_user.id` as `requester_id` to the service
3. Map `PermissionError` → `HTTP 403`

---

## API Permission Matrix

### Auth — `/api/v1/auth`

| Endpoint | Method | Unauthenticated | Any authenticated user |
|---|---|---|---|
| `/auth/register` | `POST` | ✅ Allowed | ✅ Allowed |
| `/auth/login` | `POST` | ✅ Allowed | ✅ Allowed |
| `/auth/refresh` | `POST` | ✅ Allowed (needs valid refresh token) | ✅ Allowed |

> Auth endpoints are **public** — no JWT required.

---

### Users — `/api/v1/users`

| Endpoint | Method | Unauthenticated | Authenticated user |
|---|---|---|---|
| `/users/me` | `GET` | ❌ 401 | ✅ Own profile only |
| `/users/me` | `PATCH` | ❌ 401 | ✅ Own profile only |

**Removed endpoint:**

| Endpoint | Reason removed |
|---|---|
| `GET /users` (list all users) | Exposes user directory to any authenticated user — security risk. Users should only discover others within shared projects. |

---

### Projects — `/api/v1/projects`

| Endpoint | Method | Unauthenticated | Non-member | Project MEMBER | Project ADMIN (owner) |
|---|---|---|---|---|---|
| `GET /projects` | List | ❌ 401 | — | ✅ Own projects only | ✅ Own projects only |
| `POST /projects` | Create | ❌ 401 | ✅ Any user can create | — | — |
| `GET /projects/{id}` | Read | ❌ 401 | ❌ **403** | ✅ | ✅ |
| `PATCH /projects/{id}` | Update | ❌ 401 | ❌ **403** | ❌ **403** | ✅ |
| `DELETE /projects/{id}` | Delete | ❌ 401 | ❌ **403** | ❌ **403** | ✅ |

#### Project Members sub-resource

| Endpoint | Method | Unauthenticated | Non-member | Project MEMBER | Project ADMIN |
|---|---|---|---|---|---|
| `GET /projects/{id}/members` | List members | ❌ 401 | ❌ **403** | ✅ | ✅ |
| `POST /projects/{id}/members` | Add member | ❌ 401 | ❌ **403** | ❌ **403** | ✅ |
| `PATCH /projects/{id}/members/{uid}` | Change role | ❌ 401 | ❌ **403** | ❌ **403** | ✅ (cannot change owner's role) |
| `DELETE /projects/{id}/members/{uid}` | Remove member | ❌ 401 | ❌ **403** | ❌ **403** | ✅ (cannot remove owner) |

**Special rules:**
- When a project is created, the creator is automatically added as `ADMIN` with `joined_at = now()`.
- The project owner's role **cannot be changed** (`PermissionError: "Cannot change role of project owner"`).
- The project owner **cannot be removed** from their own project.
- `GET /projects` returns **only the caller's projects** (projects they are a member of). It never returns all projects globally.

---

### Tasks — `/api/v1/projects/{project_id}/tasks`

| Endpoint | Method | Unauthenticated | Non-member | Project MEMBER | Project ADMIN |
|---|---|---|---|---|---|
| `GET /tasks` | List | ❌ 401 | ❌ **403** | ✅ | ✅ |
| `POST /tasks` | Create | ❌ 401 | ❌ **403** | ✅ | ✅ |
| `GET /tasks/{id}` | Read | ❌ 401 | ❌ **403** | ✅ | ✅ |
| `PATCH /tasks/{id}` | Update | ❌ 401 | ❌ **403** | ✅ own tasks only* | ✅ any task |
| `DELETE /tasks/{id}` | Delete | ❌ 401 | ❌ **403** | ✅ creator only** | ✅ any task |

**\* MEMBER can update a task if they are the `creator_id` OR `assignee_id`.**

**\*\* MEMBER can delete a task only if they are the `creator_id`** (not just assignee).

**Additional task rules:**
- `assignee_id` (when set) **must be a project member** — assigning to a non-member raises `400 Bad Request`.
- On status change → a WebSocket notification is sent to the `assignee_id` if connected.
- On task create/assign → a background email notification is simulated.

**Task filtering (all roles that can list):**

| Query param | Type | Effect |
|---|---|---|
| `status` | `todo \| in_progress \| done` | Filter by status |
| `priority` | `low \| medium \| high` | Filter by priority |
| `assignee_id` | `int` | Filter by assigned user |
| `sort_by` | `created_at \| due_date \| priority \| title` | Sort column |
| `sort_order` | `asc \| desc` | Sort direction |

---

### Comments — `/api/v1/tasks/{task_id}/comments`

> Note: The comment router uses a flat prefix. Membership is validated by `CommentService` which looks up the task's project and checks `project_members`.

| Endpoint | Method | Unauthenticated | Non-member | Project MEMBER | Project ADMIN |
|---|---|---|---|---|---|
| `GET /comments` | List | ❌ 401 | ❌ **403** | ✅ | ✅ |
| `POST /comments` | Create | ❌ 401 | ❌ **403** | ✅ | ✅ |
| `PATCH /comments/{id}` | Update | ❌ 401 | ❌ **403** | ✅ own only | ✅ any comment |
| `DELETE /comments/{id}` | Delete | ❌ 401 | ❌ **403** | ✅ own only | ✅ any comment |

**MEMBER can only edit/delete comments where `author_id == current_user.id`.**  
**ADMIN can edit/delete any comment in their project.**

---

### WebSocket — `/ws/notifications`

| Connection | Token valid? | In project? | Receives notifications? |
|---|---|---|---|
| Any user | ✅ Valid access JWT | ✅ Yes | ✅ Receives task status changes for tasks assigned to them |
| Any user | ✅ Valid access JWT | ❌ No | ❌ (filtered — no matching tasks) |
| Any user | ❌ Invalid/expired | — | ❌ Close code `4001` |

**Notification events pushed by server:**

```json
{
  "type": "task_status_changed",
  "task_id": 42,
  "task_title": "Implement login page",
  "new_status": "in_progress",
  "project_id": 7
}
```

The server only pushes to the `assignee_id` of the task that changed status. Multiple browser tabs for the same user all receive the message.

---

### Health — `/health`

| Endpoint | Method | Auth required |
|---|---|---|
| `/health` | `GET` | ❌ Public |

---

## Error Response Format

All permission denials return a consistent JSON body:

```json
{
  "detail": "Human-readable reason",
  "error_code": "FORBIDDEN"
}
```

| HTTP Status | `error_code` | When |
|---|---|---|
| `401 Unauthorized` | `UNAUTHORIZED` | Missing/expired/invalid JWT |
| `403 Forbidden` | `FORBIDDEN` | Valid JWT but insufficient role |
| `404 Not Found` | `NOT_FOUND` | Resource doesn't exist |
| `409 Conflict` | `CONFLICT` | Duplicate (e.g. user already a member) |
| `422 Unprocessable` | `VALIDATION_ERROR` | Pydantic validation failed |

---

## Permission Decision Flow (Pseudocode)

```
function check_permission(user, project_id, action):

    # Step 1: Must be authenticated
    if not user:
        raise 401

    # Step 2: Fetch membership
    member = project_members.get(project_id, user.id)
    is_owner = project.owner_id == user.id

    # Step 3: Route-specific rules
    match action:

        case "view_project" | "list_tasks" | "create_task"
             | "view_task" | "list_comments" | "create_comment"
             | "list_members":
            if not (is_owner or member):
                raise 403

        case "update_project" | "add_member" | "remove_member"
             | "change_member_role" | "delete_project":
            if not (is_owner or member.role == ADMIN):
                raise 403

        case "update_task":
            if not (is_owner or member.role == ADMIN):
                # must be creator or assignee
                if task.creator_id != user.id and task.assignee_id != user.id:
                    raise 403

        case "delete_task":
            if not (is_owner or member.role == ADMIN):
                # must be creator
                if task.creator_id != user.id:
                    raise 403

        case "update_comment" | "delete_comment":
            if not (is_owner or member.role == ADMIN):
                if comment.author_id != user.id:
                    raise 403
```

---

## Where the Logic Lives

| Concern | File |
|---|---|
| JWT extraction & user lookup | `src/api/dependencies.py` → `get_current_user` |
| Project membership check | `src/domain/services/project_service.py` → `require_member`, `_require_project_admin` |
| Task mutation permission | `src/domain/services/task_service.py` → `_require_task_mutator`, `_require_task_deleter` |
| Comment author check | `src/domain/services/comment_service.py` → `update_comment`, `delete_comment` |
| Routes (HTTP glue) | `src/api/v1/{projects,tasks,comments,users}.py` |

---

## Quick Reference Card

```
Legend:  ✅ Allowed   ❌ Denied   — N/A

Action                            | Unauth | Non-member | Member | Admin
----------------------------------|--------|------------|--------|------
Register / Login / Refresh        |   ✅   |     ✅     |   ✅   |  ✅
View own profile (GET /users/me)  |   ❌   |     ✅     |   ✅   |  ✅
Update own profile                |   ❌   |     ✅     |   ✅   |  ✅
List all users                    |  REMOVED — endpoint deleted
Create project                    |   ❌   |     ✅     |   ✅   |  ✅
List my projects                  |   ❌   |     —      |   ✅   |  ✅
View project details              |   ❌   |     ❌     |   ✅   |  ✅
Update project name/desc          |   ❌   |     ❌     |   ❌   |  ✅
Delete project                    |   ❌   |     ❌     |   ❌   |  ✅
List project members              |   ❌   |     ❌     |   ✅   |  ✅
Add project member                |   ❌   |     ❌     |   ❌   |  ✅
Change member role                |   ❌   |     ❌     |   ❌   |  ✅
Remove project member             |   ❌   |     ❌     |   ❌   |  ✅
List / view tasks                 |   ❌   |     ❌     |   ✅   |  ✅
Create task                       |   ❌   |     ❌     |   ✅   |  ✅
Update own task (creator/assignee)|   ❌   |     ❌     |   ✅   |  ✅
Update any task                   |   ❌   |     ❌     |   ❌   |  ✅
Delete own task (creator only)    |   ❌   |     ❌     |   ✅   |  ✅
Delete any task                   |   ❌   |     ❌     |   ❌   |  ✅
List / read comments              |   ❌   |     ❌     |   ✅   |  ✅
Create comment                    |   ❌   |     ❌     |   ✅   |  ✅
Edit own comment                  |   ❌   |     ❌     |   ✅   |  ✅
Edit any comment                  |   ❌   |     ❌     |   ❌   |  ✅
Delete own comment                |   ❌   |     ❌     |   ✅   |  ✅
Delete any comment                |   ❌   |     ❌     |   ❌   |  ✅
WebSocket connect                 |   ❌   |     ✅*    |   ✅   |  ✅
Receive WS task notification      |   ❌   |     ❌     |   ✅** |  ✅**

* WS connection is accepted for any valid token; no project check at connect time.
** Notifications are sent only for tasks where the user is the assignee.
```
