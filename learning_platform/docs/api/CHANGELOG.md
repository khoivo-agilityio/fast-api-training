# API Changelog

All endpoints introduced in this project, organized by phase.

Base URL: `/api/v1`

---

## v1.0.0 — Initial Release

### Phase 1 — Auth & Users

#### Authentication (`/auth`)

| Method | Path | Auth | Status | Description |
|---|---|---|---|---|
| `POST` | `/auth/register` | ❌ | 201 | Register a new user (defaults to `student` role). Returns access + refresh tokens. |
| `POST` | `/auth/login` | ❌ | 200 | Login with email + password. Returns access + refresh tokens. |
| `POST` | `/auth/refresh` | ❌ | 200 | Exchange a valid refresh token for a new token pair. |
| `POST` | `/auth/logout` | ✅ Bearer | 200 | Blacklist the current access token in Redis. |

**Register request body:**
```json
{
  "email": "alice@example.com",
  "password": "SecurePass123!",
  "display_name": "Alice Smith"
}
```

**Token response:**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

#### Users (`/users`)

| Method | Path | Auth | Status | Description |
|---|---|---|---|---|
| `GET` | `/users/me` | ✅ Bearer | 200 | Get the current user's profile. |
| `PATCH` | `/users/me` | ✅ Bearer | 200 | Update profile fields (display_name, avatar, password). Partial update. |

---

### Phase 2 — Courses, Lessons, Enrollment

#### Courses (`/courses`)

| Method | Path | Auth | Roles | Status | Description |
|---|---|---|---|---|---|
| `POST` | `/courses` | ✅ | Instructor, Admin | 201 | Create a new course. |
| `GET` | `/courses` | ✅ | Any | 200 | List courses (paginated). Supports `?search=`, `?instructor=`, `?limit=`, `?offset=`. |
| `GET` | `/courses/{id}` | ✅ | Any | 200 | Get a course by ID. |
| `PATCH` | `/courses/{id}` | ✅ | Instructor (own), Admin | 200 | Update a course. |
| `DELETE` | `/courses/{id}` | ✅ | Admin | 204 | Delete a course. |
| `POST` | `/courses/{id}/enroll` | ✅ | Student | 201 | Enroll in a course. |

**Course create request:**
```json
{
  "title": "Introduction to Python",
  "description": "A beginner-friendly Python course."
}
```

#### Lessons (`/courses/{course_id}/lessons`, `/lessons`)

| Method | Path | Auth | Roles | Status | Description |
|---|---|---|---|---|---|
| `POST` | `/courses/{course_id}/lessons` | ✅ | Instructor (own), Admin | 201 | Create a lesson in a course. |
| `GET` | `/courses/{course_id}/lessons` | ✅ | Any enrolled | 200 | List all lessons in a course ordered by `order`. |
| `GET` | `/lessons/{id}` | ✅ | Enrolled, Instructor, Admin | 200 | Get a lesson. Triggers auto-completion for students if the lesson has no quiz. |
| `PATCH` | `/lessons/{id}` | ✅ | Instructor (own), Admin | 200 | Update lesson fields. |
| `DELETE` | `/lessons/{id}` | ✅ | Instructor (own), Admin | 204 | Delete a lesson (cascades to quiz + progress). |

**Lesson create request:**
```json
{
  "title": "Variables and Data Types",
  "content": "In Python, variables are dynamically typed...",
  "order": 1
}
```

---

### Phase 3 — Quizzes, Submissions, Grading

#### Quizzes (`/lessons/{lesson_id}/quiz`, `/quizzes/{quiz_id}/questions`, `/questions`)

| Method | Path | Auth | Roles | Status | Description |
|---|---|---|---|---|---|
| `POST` | `/lessons/{lesson_id}/quiz` | ✅ | Instructor (own), Admin | 201 | Create a quiz for a lesson (one per lesson). |
| `GET` | `/lessons/{lesson_id}/quiz` | ✅ | Any enrolled | 200 | Get quiz with questions. Students see questions without `correct_answer`. |
| `PATCH` | `/lessons/{lesson_id}/quiz` | ✅ | Instructor (own), Admin | 200 | Update quiz metadata. |
| `DELETE` | `/lessons/{lesson_id}/quiz` | ✅ | Instructor (own), Admin | 204 | Delete quiz (cascades to questions). |
| `POST` | `/quizzes/{quiz_id}/questions` | ✅ | Instructor, Admin | 201 | Add a question to a quiz. |
| `PATCH` | `/questions/{id}` | ✅ | Instructor, Admin | 200 | Update a question. |
| `DELETE` | `/questions/{id}` | ✅ | Instructor, Admin | 204 | Delete a question. |

**Quiz create request:**
```json
{
  "title": "Python Basics Quiz",
  "description": "Test your knowledge of Python fundamentals.",
  "time_limit_minutes": 30
}
```

**Question create request (MCQ):**
```json
{
  "text": "What is the output of type([])?",
  "type": "mcq",
  "options": ["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'set'>"],
  "correct_answer": "<class 'list'>"
}
```

#### Submissions (`/quizzes/{quiz_id}/submit`, `/quizzes/{quiz_id}/submission`)

| Method | Path | Auth | Roles | Status | Description |
|---|---|---|---|---|---|
| `POST` | `/quizzes/{quiz_id}/submit` | ✅ | Student (enrolled) | 201 | Submit answers. Auto-graded. One attempt per quiz. Triggers lesson/course progress update if passed. |
| `GET` | `/quizzes/{quiz_id}/submission` | ✅ | Student (own) | 200 | Get own submission result with per-answer correctness. |

**Submit quiz request:**
```json
{
  "answers": [
    {
      "question_id": "<uuid>",
      "answer": "<class 'list'>"
    }
  ]
}
```

**Submission response:**
```json
{
  "id": "<uuid>",
  "quiz_id": "<uuid>",
  "score": 100.0,
  "passed": true,
  "submitted_at": "2026-05-11T07:00:00Z",
  "answers": [
    {
      "question_id": "<uuid>",
      "answer": "<class 'list'>",
      "is_correct": true
    }
  ]
}
```

---

### Phase 4 — Progress Tracking

#### Progress (`/courses/{course_id}/progress`, `/progress`)

| Method | Path | Auth | Roles | Status | Description |
|---|---|---|---|---|---|
| `GET` | `/courses/{course_id}/progress` | ✅ | Student (own) | 200 | Get progress for a specific enrolled course. |
| `GET` | `/progress` | ✅ | Student | 200 | Get progress across all enrolled courses. |

**Course progress response:**
```json
{
  "course_id": "<uuid>",
  "completed_lessons": 3,
  "total_lessons": 5,
  "percent_complete": 60.0,
  "is_complete": false
}
```

---

### Phase 5 — Admin Features

#### Admin — Users (`/admin/users`)

| Method | Path | Auth | Status | Description |
|---|---|---|---|---|
| `GET` | `/admin/users` | ✅ Admin | 200 | List all users (paginated). |
| `GET` | `/admin/users/{id}` | ✅ Admin | 200 | Get any user by ID. |
| `PATCH` | `/admin/users/{id}` | ✅ Admin | 200 | Update any user's profile. |
| `DELETE` | `/admin/users/{id}` | ✅ Admin | 204 | Delete a user. |

#### Admin — Courses (`/admin/courses`)

| Method | Path | Auth | Status | Description |
|---|---|---|---|---|
| `GET` | `/admin/courses` | ✅ Admin | 200 | List all courses (paginated). |
| `GET` | `/admin/courses/{id}` | ✅ Admin | 200 | Get any course by ID. |
| `PATCH` | `/admin/courses/{id}` | ✅ Admin | 200 | Update any course (skips ownership check). |
| `DELETE` | `/admin/courses/{id}` | ✅ Admin | 204 | Delete any course. |

#### Admin — Submissions (`/admin/submissions`)

| Method | Path | Auth | Status | Description |
|---|---|---|---|---|
| `GET` | `/admin/submissions` | ✅ Admin | 200 | List all submissions (paginated). |
| `DELETE` | `/admin/submissions/{id}` | ✅ Admin | 204 | Delete a submission. |

#### Admin — Progress (`/admin/progress`)

| Method | Path | Auth | Status | Description |
|---|---|---|---|---|
| `GET` | `/admin/progress` | ✅ Admin | 200 | List all progress records (paginated). |

#### Admin UI

| Path | Description |
|---|---|
| `/admin` | SQLAdmin web UI (session-based auth, admin credentials required). |

---

### System

| Method | Path | Auth | Status | Description |
|---|---|---|---|---|
| `GET` | `/health` | ❌ | 200 | Returns `{"status": "healthy"}`. |

---

## Standard Error Response

All error responses follow this shape:

```json
{
  "detail": "Human-readable message",
  "error_code": "MACHINE_READABLE_CODE"
}
```

### Error Codes

| Code | HTTP | Description |
|---|---|---|
| `INVALID_CREDENTIALS` | 401 | Wrong email or password |
| `EMAIL_ALREADY_REGISTERED` | 409 | Duplicate email on register |
| `TOKEN_EXPIRED` | 401 | JWT has expired |
| `TOKEN_INVALID` | 401 | Malformed or tampered JWT |
| `TOKEN_REVOKED` | 401 | Token was blacklisted after logout |
| `INSUFFICIENT_PERMISSIONS` | 403 | User lacks required role |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Generic conflict (e.g. duplicate enrollment) |
| `QUIZ_ALREADY_EXISTS` | 409 | Lesson already has a quiz |
| `ALREADY_SUBMITTED` | 409 | Student has already submitted this quiz |
| `NOT_ENROLLED` | 403 | Student is not enrolled in the course |
