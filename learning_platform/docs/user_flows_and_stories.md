# AI-Enhanced Learning Platform — User Flows & User Stories

**Target AI Agent**: Claude Sonnet 4.6  
**Date**: April 23, 2026  
**Author**: KhoiVo  
**Source**: `learning_platform/docs/analysys_plan.md`  
**Purpose**: Input for Mermaid flow diagram generation

---

## Personas

| ID | Persona | Description |
|----|---------|-------------|
| P1 | **Admin** | Platform administrator. Full CRUD on all entities. Manages users, courses, and platform health. |
| P2 | **Instructor** | Creates and manages own courses, lessons, and quizzes. Views student submissions. |
| P3 | **Student** | Enrolls in published courses, studies lessons, takes quizzes, tracks own progress. |
| P4 | **Guest** | Unauthenticated visitor. Can only reach `/health` and auth endpoints. |

---

## Feature Groups

| # | Feature Group | Personas |
|---|---------------|----------|
| F1 | Authentication & Token Management | All |
| F2 | User Profile Management | Admin, Instructor, Student |
| F3 | Course Management | Admin, Instructor |
| F4 | Course Discovery & Enrollment | Student |
| F5 | Lesson Management | Admin, Instructor |
| F6 | Lesson Viewing & Completion (no quiz) | Student |
| F7 | Quiz & Question Management | Admin, Instructor |
| F8 | Quiz Taking & Auto-grading | Student |
| F9 | Progress Tracking | Student |
| F10 | Admin Panel (REST + SQLAdmin UI) | Admin |

---

## F1 — Authentication & Token Management

### User Stories

| ID | Story |
|----|-------|
| US-F1-01 | As a **Guest**, I want to register with email, username, and password so that I can access the platform. |
| US-F1-02 | As a **Guest**, I want to log in with email and password so that I receive access and refresh tokens. |
| US-F1-03 | As an **authenticated user**, I want to refresh my access token using my refresh token so that I stay logged in without re-entering my credentials. |
| US-F1-04 | As an **authenticated user**, I want to log out so that my token is invalidated and no one else can use it. |
| US-F1-05 | As a **Guest**, I want to be blocked from accessing protected endpoints without a token so that the platform is secure. |

### Flow: F1 — Registration

```
start: Guest visits /auth/register
  → submits: email, username, password, full_name (optional)
  → system: validate uniqueness (email, username)
    [conflict] → 409 ConflictError: "Email already registered"
    [ok]       → hash password → create user (role=student) → generate access+refresh tokens
               → return: TokenResponse (200)
```

### Flow: F1 — Login

```
start: User visits /auth/login
  → submits: email, password
  → system: look up user by email
    [not found]       → 401 AuthorizationError: "Invalid credentials"
    [found, inactive] → 403: "Account inactive"
    [found, active]   → verify password hash
      [wrong password] → 401: "Invalid credentials"
      [correct]        → generate access+refresh tokens
                       → return: TokenResponse (200)
```

### Flow: F1 — Token Refresh

```
start: Client sends POST /auth/refresh { refresh_token }
  → system: decode refresh token
    [expired / invalid] → 401: "Invalid or expired refresh token"
    [blacklisted]       → 401: "Token already revoked"
    [valid]             → blacklist old refresh token in Redis
                        → generate new access+refresh tokens
                        → return: TokenResponse (200)
```

### Flow: F1 — Logout

```
start: Client sends POST /auth/logout (Bearer access_token)
  → system: decode access token → add jti to Redis blacklist (TTL = token expiry)
  → return: 204 No Content
```

---

## F2 — User Profile Management

### User Stories

| ID | Story |
|----|-------|
| US-F2-01 | As an **authenticated user**, I want to view my own profile so that I can see my account details. |
| US-F2-02 | As an **authenticated user**, I want to update my full name, email, or password so that I can keep my account current. |

### Flow: F2 — View Profile

```
start: GET /users/me (Bearer token)
  → system: extract user_id from token
    [blacklisted token] → 401
    [valid]             → fetch user by id → return: UserResponse (200)
```

### Flow: F2 — Update Profile

```
start: PATCH /users/me { full_name?, email?, password? }
  → system: validate request (at least one field)
  → if email change: check uniqueness
    [conflict] → 409: "Email already in use"
    [ok]       → apply changes → return: UserResponse (200)
```

---

## F3 — Course Management (Instructor / Admin)

### User Stories

| ID | Story |
|----|-------|
| US-F3-01 | As an **Instructor**, I want to create a course with title and description so that I can offer it to students. |
| US-F3-02 | As an **Instructor**, I want to update my own course so that I can keep the content current. |
| US-F3-03 | As an **Admin**, I want to delete any course so that I can remove inappropriate content. |
| US-F3-04 | As an **Instructor**, I want to publish my course so that students can discover and enroll in it. |
| US-F3-05 | As an **Instructor or Admin**, I want to list all my courses with pagination so that I can manage them easily. |

### Flow: F3 — Create Course

```
start: POST /courses { title, description? } (Instructor or Admin)
  → RBAC check: role must be instructor or admin
    [denied] → 403
    [ok]     → create course (instructor_id = current_user.id, is_published=false)
             → return: CourseResponse 201
```

### Flow: F3 — Publish Course

```
start: POST /courses/{id}/publish (Instructor or Admin)
  → fetch course by id
    [not found]             → 404
    [not owner + not admin] → 403
    [already published]     → 409: "Course already published"
    [ok]                    → set is_published=true → return: CourseResponse 200
```

### Flow: F3 — Update / Delete Course

```
start: PATCH /courses/{id} or DELETE /courses/{id}
  → fetch course
    [not found]                  → 404
    [PATCH: not owner+not admin] → 403
    [DELETE: not admin]          → 403
    [ok]                         → apply changes / delete → 200 / 204
```

---

## F4 — Course Discovery & Enrollment (Student)

### User Stories

| ID | Story |
|----|-------|
| US-F4-01 | As a **Student**, I want to browse published courses with search and pagination so that I can find courses to enroll in. |
| US-F4-02 | As a **Student**, I want to view a course's detail page so that I can decide whether to enroll. |
| US-F4-03 | As a **Student**, I want to enroll in a published course so that I can access its lessons. |
| US-F4-04 | As a **Student**, I want to be prevented from enrolling twice in the same course so that I don't get duplicate records. |

### Flow: F4 — Browse Courses

```
start: GET /courses?search=?&is_published=true&limit=20&offset=0
  → system: apply filters + pagination
  → return: CourseListResponse 200
```

### Flow: F4 — Enroll in Course

```
start: POST /courses/{id}/enroll (Student)
  → RBAC: must be student
    [denied] → 403
  → fetch course
    [not found]      → 404
    [not published]  → 400: "Course is not published"
  → check existing enrollment
    [already enrolled] → 409: "Already enrolled"
    [ok]               → create Enrollment record
                       → create CourseProgress record (total_lessons = count of lessons, completed=0)
                       → return: EnrollmentResponse 201
```

---

## F5 — Lesson Management (Instructor / Admin)

### User Stories

| ID | Story |
|----|-------|
| US-F5-01 | As an **Instructor**, I want to add a text lesson to my course so that students have content to study. |
| US-F5-02 | As an **Instructor**, I want to update a lesson's title, content, or order so that I can improve the course. |
| US-F5-03 | As an **Instructor or Admin**, I want to delete a lesson so that I can remove outdated content. |
| US-F5-04 | As an **Instructor**, I want to list all lessons in my course so that I can manage them. |

### Flow: F5 — Create Lesson

```
start: POST /courses/{course_id}/lessons { title, content, order_index? }
  → fetch course
    [not found]             → 404
    [not owner + not admin] → 403
  → create lesson (text-only)
  → recalculate total_lessons in all CourseProgress records for this course
  → return: LessonResponse 201
```

### Flow: F5 — Update / Delete Lesson

```
start: PATCH /lessons/{id} or DELETE /lessons/{id}
  → fetch lesson → fetch parent course
    [not found]             → 404
    [not owner + not admin] → 403
    [ok PATCH]              → apply changes → return: LessonResponse 200
    [ok DELETE]             → delete lesson (cascade: quiz, lesson_progress)
                            → recalculate total_lessons in CourseProgress
                            → return: 204
```

---

## F6 — Lesson Viewing & Auto-Completion (Student)

### User Stories

| ID | Story |
|----|-------|
| US-F6-01 | As a **Student**, I want to list all lessons in a course I'm enrolled in so that I know what to study. |
| US-F6-02 | As a **Student**, I want to view a lesson's content so that I can learn from it. |
| US-F6-03 | As a **Student**, I want a lesson without a quiz to be marked complete automatically when I view it so that my progress is tracked. |

### Flow: F6 — View Lesson (triggers completion if no quiz)

```
start: GET /lessons/{id} (Student)
  → fetch lesson
    [not found] → 404
  → check enrollment in lesson's course
    [not enrolled] → 403: "Not enrolled in this course"
  → does lesson have a quiz?
    [YES, has quiz]
      → return: LessonResponse 200 (no completion side-effect here)
    [NO quiz]
      → check existing lesson_progress for (student_id, lesson_id)
        [already complete] → return: LessonResponse 200 (idempotent)
        [not complete]     → mark lesson_progress.completed = true
                           → call ProgressService.recalculate(student_id, course_id)
                           → return: LessonResponse 200
```

---

## F7 — Quiz & Question Management (Instructor / Admin)

### User Stories

| ID | Story |
|----|-------|
| US-F7-01 | As an **Instructor**, I want to create a quiz for a lesson so that students can be assessed. |
| US-F7-02 | As an **Instructor**, I want to add single-choice or multiple-choice questions to a quiz. |
| US-F7-03 | As an **Instructor**, I want to mark which answer options are correct so that the system can auto-grade. |
| US-F7-04 | As an **Instructor**, I want to set a passing score threshold so that I control what counts as "passed". |
| US-F7-05 | As an **Instructor**, I want to update or delete quiz questions so that I can refine assessments. |
| US-F7-06 | As a **Student**, I want to see quiz questions without the correct answer flags so that I'm not given the answers. |

### Flow: F7 — Create Quiz + Questions

```
start: POST /lessons/{lesson_id}/quiz { title, passing_score=70 }
  → fetch lesson
    [not found]             → 404
    [not owner + not admin] → 403
  → check quiz already exists for this lesson
    [exists] → 409: "Quiz already exists for this lesson"
    [ok]     → create Quiz
             → return: QuizResponse 201

next: POST /quizzes/{quiz_id}/questions { text, question_type, options: [{text, is_correct}], order_index }
  → fetch quiz → verify ownership
  → validate: single_choice must have exactly 1 correct option
              multiple_choice must have ≥ 1 correct option
    [invalid] → 422
    [ok]      → create Question + AnswerOptions
              → return: QuestionResponse 201
```

### Flow: F7 — Student Views Quiz (is_correct hidden)

```
start: GET /lessons/{lesson_id}/quiz (Student)
  → fetch quiz + questions + answer_options
  → serialize using QuizDetailResponse
    → AnswerOptionResponse (id, text only — no is_correct)
  → return 200
```

---

## F8 — Quiz Taking & Auto-grading (Student)

### User Stories

| ID | Story |
|----|-------|
| US-F8-01 | As a **Student**, I want to submit answers to a quiz so that I can be graded. |
| US-F8-02 | As a **Student**, I want the system to auto-grade my submission so that I get immediate feedback. |
| US-F8-03 | As a **Student**, I want to know whether I passed or failed the quiz based on the passing score. |
| US-F8-04 | As a **Student**, I want my quiz submission to be blocked if I've already submitted once so that I don't re-attempt. |
| US-F8-05 | As a **Student**, I want my lesson to be marked complete automatically when I pass the quiz. |
| US-F8-06 | As a **Student**, I want to view my submission result with a per-question breakdown. |

### Flow: F8 — Submit Quiz

```
start: POST /quizzes/{quiz_id}/submit { answers: [{question_id, selected_option_ids}] }
  → fetch quiz
    [not found] → 404
  → check student enrolled in quiz's course
    [not enrolled] → 403
  → check existing submission for (student_id, quiz_id)
    [already submitted] → 409: "Already submitted"
  → validate all question_ids belong to this quiz
    [invalid] → 422
  → AUTO-GRADE:
      for each question:
        fetch correct option ids from answer_options where is_correct=true
        compare with student's selected_option_ids
        single_choice:   correct if selected == correct (exact match, 1 option)
        multiple_choice: correct if selected set == correct set (all-or-nothing)
        record: is_correct = true/false per question
      score = (correct_count / total_questions) * 100
      passed = score >= quiz.passing_score
  → save Submission (score, passed, submitted_at)
  → save SubmissionAnswers (one row per question with selected_option_ids + is_correct)
  → if passed:
      mark lesson_progress.completed = true for (student_id, lesson_id)
      call ProgressService.recalculate(student_id, course_id)
  → return: SubmissionDetailResponse 201
```

### Flow: F8 — View My Submission

```
start: GET /quizzes/{quiz_id}/submission (Student)
  → fetch submission for (student_id, quiz_id)
    [not found] → 404: "No submission found"
    [found]     → return: SubmissionDetailResponse 200
```

---

## F9 — Progress Tracking (Student)

### User Stories

| ID | Story |
|----|-------|
| US-F9-01 | As a **Student**, I want to view my progress for a specific course so that I know how far along I am. |
| US-F9-02 | As a **Student**, I want to view progress across all my enrolled courses so that I get an overview of my learning. |
| US-F9-03 | As a **Student**, I want to see a course marked as "complete" when all lessons are done. |

### Flow: F9 — View Course Progress

```
start: GET /courses/{course_id}/progress (Student)
  → fetch CourseProgress for (student_id, course_id)
    [not found] → 404: "Not enrolled or no progress record"
    [found]     → return: CourseProgressResponse 200
                   { course_id, completed_lessons, total_lessons,
                     percent_complete, is_complete }
```

### Flow: F9 — Progress Recalculation (internal, triggered by F6 / F8)

```
trigger: ProgressService.recalculate(student_id, course_id)
  → count lesson_progress rows where student_id=X AND lesson_id IN (course lessons) AND completed=true
  → count total lessons in course
  → percent_complete = (completed / total) * 100
  → is_complete = (completed == total AND total > 0)
  → upsert CourseProgress record
```

### Flow: F9 — View All Enrolled Courses Progress

```
start: GET /progress (Student)
  → fetch all CourseProgress records where student_id = current_user.id
  → return: CourseProgressListResponse 200
```

---

## F10 — Admin Panel (REST + SQLAdmin UI)

### User Stories

| ID | Story |
|----|-------|
| US-F10-01 | As an **Admin**, I want to list and search all users so that I can manage the user base. |
| US-F10-02 | As an **Admin**, I want to update any user's role or active status so that I can control access. |
| US-F10-03 | As an **Admin**, I want to list and manage all courses regardless of instructor so that I can oversee content. |
| US-F10-04 | As an **Admin**, I want to view and delete any submission so that I can handle abuse cases. |
| US-F10-05 | As an **Admin**, I want to view all learning progress records so that I can audit platform activity. |
| US-F10-06 | As an **Admin**, I want to use the SQLAdmin web UI to manage entities visually. |
| US-F10-07 | As a **non-Admin**, I want to be blocked from all `/admin/*` endpoints so that sensitive operations are protected. |

### Flow: F10 — Admin REST Endpoints

```
start: Any request to /admin/* or /api/v1/admin/*
  → RBAC check: current_user.role == admin
    [not admin] → 403: "Admin access required"
    [admin]     → proceed to specific handler

GET  /admin/users          → paginated list of all users
GET  /admin/users/{id}     → user detail
PATCH /admin/users/{id}    → update role / is_active
DELETE /admin/users/{id}   → soft-delete or hard-delete user

GET  /admin/courses        → paginated list of all courses
PATCH /admin/courses/{id}  → update any course
DELETE /admin/courses/{id} → delete any course

GET  /admin/submissions    → paginated list of all submissions
DELETE /admin/submissions/{id} → delete submission (resets quiz attempt)

GET  /admin/progress       → paginated list of all CourseProgress records
```

### Flow: F10 — SQLAdmin UI Access

```
start: GET /admin (browser)
  → SQLAdmin mounts at /admin
  → Basic auth or session-based check (Admin role)
    [unauthorized] → redirect to /admin/login
    [authorized]   → render SQLAdmin dashboard with entity tables:
                     Users | Courses | Lessons | Quizzes | Submissions | Progress
```

---

## Summary: Flow Dependency Map

This map shows what triggers what — useful for generating Mermaid sequence diagrams.

```
Registration / Login
  └─→ Token issued
        └─→ All authenticated flows unlocked

Student enrolls in course
  └─→ CourseProgress record created (total_lessons set)

Student views lesson (no quiz)
  └─→ LessonProgress.completed = true
        └─→ ProgressService.recalculate()
              └─→ CourseProgress updated (percent, is_complete)

Student submits quiz → passes
  └─→ Submission saved
        └─→ LessonProgress.completed = true
              └─→ ProgressService.recalculate()
                    └─→ CourseProgress updated

Instructor creates lesson
  └─→ total_lessons recalculated for all enrolled students' CourseProgress

Instructor deletes lesson
  └─→ lesson_progress rows cascaded deleted
        └─→ total_lessons recalculated for all enrolled students' CourseProgress
```

---

## Acceptance Criteria Summary

| User Story | Given | When | Then |
|---|---|---|---|
| US-F1-01 | Guest provides valid unique email + username | POST /auth/register | 200 + access & refresh tokens |
| US-F1-01 | Email already exists | POST /auth/register | 409 ConflictError |
| US-F1-02 | Valid credentials | POST /auth/login | 200 + tokens |
| US-F1-02 | Wrong password | POST /auth/login | 401 |
| US-F1-03 | Valid non-expired refresh token | POST /auth/refresh | 200 + new token pair; old refresh token blacklisted |
| US-F1-04 | Valid access token | POST /auth/logout | 204; token added to Redis blacklist |
| US-F4-03 | Student enrolled, course published | POST /courses/{id}/enroll | 201 + CourseProgress created |
| US-F4-04 | Student already enrolled | POST /courses/{id}/enroll | 409 |
| US-F6-03 | Student views lesson with no quiz, not yet completed | GET /lessons/{id} | 200 + lesson_progress.completed=true + course progress updated |
| US-F8-01 | Student submits correct answers | POST /quizzes/{id}/submit | 201, score=100, passed=true |
| US-F8-04 | Student submits again | POST /quizzes/{id}/submit | 409 |
| US-F8-05 | Student passes quiz | POST /quizzes/{id}/submit | lesson_progress.completed=true |
| US-F9-03 | All lessons completed | GET /courses/{id}/progress | percent_complete=100, is_complete=true |
| US-F10-07 | Non-admin hits /admin/* | Any admin endpoint | 403 |

---

## Mermaid Flow Diagrams

> **Diagram conventions**
> - 🔴 `errorState` — error / rejection nodes
> - 🟢 `successState` — success / response nodes
> - 🔵 `processState` — action / processing nodes
> - 🟠 `decisionState` — branch / decision nodes

---

### F1 — Authentication & Token Management

```mermaid
---
config:
  layout: elk
  theme: mc
---
flowchart TD
    subgraph REG["📋 Register — POST /auth/register"]
        A1[Guest visits<br/>POST /auth/register] --> A2[Submit email, username,<br/>password, full_name?]
        A2 --> A3{Validate uniqueness<br/>email + username}
        A3 -->|Taken| A4[409 ConflictError<br/>Email already registered]
        A3 -->|Unique| A5[Hash password]
        A5 --> A6[Create user — role = student]
        A6 --> A7[Generate access + refresh tokens]
        A7 --> A8[Return TokenResponse 200 OK]
    end

    subgraph LOGIN["🔑 Login — POST /auth/login"]
        B1[User visits<br/>POST /auth/login] --> B2[Submit email & password]
        B2 --> B3{Look up user<br/>by email}
        B3 -->|Not found| B4[401 Invalid credentials]
        B3 -->|Found, inactive| B5[403 Account inactive]
        B3 -->|Found, active| B6{Verify<br/>password hash}
        B6 -->|Wrong password| B7[401 Invalid credentials]
        B6 -->|Correct| B8[Generate access + refresh tokens]
        B8 --> B9[Return TokenResponse 200 OK]
    end

    subgraph REFRESH["🔄 Refresh — POST /auth/refresh"]
        C1[Client sends<br/>POST /auth/refresh] --> C2[Decode refresh token]
        C2 --> C3{Token valid?}
        C3 -->|Expired / invalid| C4[401 Invalid or expired token]
        C3 -->|Blacklisted| C5[401 Token already revoked]
        C3 -->|Valid| C6[Blacklist old refresh token in Redis]
        C6 --> C7[Generate new access + refresh tokens]
        C7 --> C8[Return TokenResponse 200 OK]
    end

    subgraph LOGOUT["🚪 Logout — POST /auth/logout"]
        D1[Client sends<br/>POST /auth/logout] --> D2[Decode access token]
        D2 --> D3[Add token to Redis blacklist<br/>TTL = token expiry]
        D3 --> D4[Return 204 No Content]
    end

    classDef errorState   stroke:#f87171,fill:#fef2f2,color:#1e1b4b
    classDef successState stroke:#4ade80,fill:#f0fdf4,color:#1e1b4b
    classDef processState stroke:#38bdf8,fill:#f0f9ff,color:#1e1b4b
    classDef decisionState stroke:#fb923c,fill:#fff7ed,color:#1e1b4b

    class A4,B4,B5,B7,C4,C5 errorState
    class A8,B9,C8,D4 successState
    class A1,A2,A5,A6,A7,B1,B2,B8,C1,C2,C6,C7,D1,D2,D3 processState
    class A3,B3,B6,C3 decisionState
```

---

### F2 — User Profile Management

```mermaid
---
config:
  layout: elk
  theme: mc
---
flowchart TD
    subgraph VIEW["👤 View Profile — GET /users/me"]
        A1[GET /users/me<br/>Bearer token] --> A2[Extract user_id from token]
        A2 --> A3{Token blacklisted?}
        A3 -->|Yes| A4[401 Unauthorized]
        A3 -->|No| A5[Fetch user by id]
        A5 --> A6[Return UserResponse 200 OK]
    end

    subgraph UPDATE["✏️ Update Profile — PATCH /users/me"]
        B1[PATCH /users/me<br/>full_name? email? password?] --> B2{Email<br/>changing?}
        B2 -->|Yes| B3[Check email uniqueness]
        B3 -->|Taken| B4[409 ConflictError<br/>Email already in use]
        B3 -->|Unique| B5[Apply changes]
        B2 -->|No| B5
        B5 --> B6[Return UserResponse 200 OK]
    end

    classDef errorState   stroke:#f87171,fill:#fef2f2,color:#1e1b4b
    classDef successState stroke:#4ade80,fill:#f0fdf4,color:#1e1b4b
    classDef processState stroke:#38bdf8,fill:#f0f9ff,color:#1e1b4b
    classDef decisionState stroke:#fb923c,fill:#fff7ed,color:#1e1b4b

    class A4,B4 errorState
    class A6,B6 successState
    class A1,A2,A5,B1,B3,B5 processState
    class A3,B2 decisionState
```

---

### F3 — Course Management

```mermaid
---
config:
  layout: elk
  theme: mc
---
flowchart TD
    subgraph CREATE["➕ Create Course — POST /courses"]
        A1[POST /courses<br/>title, description?] --> A2{RBAC check<br/>instructor or admin?}
        A2 -->|Denied| A3[403 Forbidden]
        A2 -->|Allowed| A4[Create course<br/>is_published = false]
        A4 --> A5[Return CourseResponse 201 Created]
    end

    subgraph PUBLISH["📢 Publish Course — POST /courses/id/publish"]
        B1[POST /courses/id/publish] --> B2[Fetch course by id]
        B2 --> B3{Found?}
        B3 -->|Not found| B4[404 Not Found]
        B3 -->|Found| B5{Owner or admin?}
        B5 -->|No| B6[403 Forbidden]
        B5 -->|Yes| B7{Already published?}
        B7 -->|Yes| B8[409 ConflictError<br/>Course already published]
        B7 -->|No| B9[Set is_published = true]
        B9 --> B10[Return CourseResponse 200 OK]
    end

    subgraph EDIT["✏️ Update / Delete Course — PATCH or DELETE /courses/id"]
        C1[PATCH or DELETE<br/>/courses/id] --> C2[Fetch course]
        C2 --> C3{Found?}
        C3 -->|Not found| C4[404 Not Found]
        C3 -->|Found| C5{Action?}
        C5 -->|PATCH| C6{Owner or admin?}
        C6 -->|No| C7[403 Forbidden]
        C6 -->|Yes| C8[Apply changes]
        C8 --> C9[Return CourseResponse 200 OK]
        C5 -->|DELETE| C10{Is admin?}
        C10 -->|No| C11[403 Forbidden]
        C10 -->|Yes| C12[Delete course]
        C12 --> C13[Return 204 No Content]
    end

    classDef errorState   stroke:#f87171,fill:#fef2f2,color:#1e1b4b
    classDef successState stroke:#4ade80,fill:#f0fdf4,color:#1e1b4b
    classDef processState stroke:#38bdf8,fill:#f0f9ff,color:#1e1b4b
    classDef decisionState stroke:#fb923c,fill:#fff7ed,color:#1e1b4b

    class A3,B4,B6,B8,C4,C7,C11 errorState
    class A5,B10,C9,C13 successState
    class A1,A4,B1,B2,B9,C1,C2,C8,C12 processState
    class A2,B3,B5,B7,C3,C5,C6,C10 decisionState
```

---

### F4 — Course Discovery & Enrollment

```mermaid
---
config:
  layout: elk
  theme: mc
---
flowchart TD
    subgraph BROWSE["🔍 Browse Courses — GET /courses"]
        A1[GET /courses<br/>search? is_published? limit offset] --> A2[Apply filters + pagination]
        A2 --> A3[Return CourseListResponse 200 OK]
    end

    subgraph ENROLL["🎓 Enroll in Course — POST /courses/id/enroll"]
        B1[POST /courses/id/enroll<br/>Student] --> B2{RBAC check<br/>student role?}
        B2 -->|Denied| B3[403 Forbidden]
        B2 -->|Allowed| B4[Fetch course]
        B4 --> B5{Found?}
        B5 -->|Not found| B6[404 Not Found]
        B5 -->|Found| B7{Is published?}
        B7 -->|No| B8[400 Bad Request<br/>Course is not published]
        B7 -->|Yes| B9{Already enrolled?}
        B9 -->|Yes| B10[409 ConflictError<br/>Already enrolled]
        B9 -->|No| B11[Create Enrollment record]
        B11 --> B12[Create CourseProgress record<br/>completed = 0, total = lesson count]
        B12 --> B13[Return EnrollmentResponse 201 Created]
    end

    classDef errorState   stroke:#f87171,fill:#fef2f2,color:#1e1b4b
    classDef successState stroke:#4ade80,fill:#f0fdf4,color:#1e1b4b
    classDef processState stroke:#38bdf8,fill:#f0f9ff,color:#1e1b4b
    classDef decisionState stroke:#fb923c,fill:#fff7ed,color:#1e1b4b

    class B3,B6,B8,B10 errorState
    class A3,B13 successState
    class A1,A2,B1,B4,B11,B12 processState
    class B2,B5,B7,B9 decisionState
```

---

### F5 — Lesson Management

```mermaid
---
config:
  layout: elk
  theme: mc
---
flowchart TD
    subgraph CREATE["➕ Create Lesson — POST /courses/course_id/lessons"]
        A1[POST /courses/course_id/lessons<br/>title, content, order_index?] --> A2[Fetch course]
        A2 --> A3{Found?}
        A3 -->|Not found| A4[404 Not Found]
        A3 -->|Found| A5{Owner or admin?}
        A5 -->|No| A6[403 Forbidden]
        A5 -->|Yes| A7[Create lesson]
        A7 --> A8[Recalculate total_lessons<br/>in all CourseProgress for this course]
        A8 --> A9[Return LessonResponse 201 Created]
    end

    subgraph EDIT["✏️ Update / Delete Lesson — PATCH or DELETE /lessons/id"]
        B1[PATCH or DELETE<br/>/lessons/id] --> B2[Fetch lesson + parent course]
        B2 --> B3{Found?}
        B3 -->|Not found| B4[404 Not Found]
        B3 -->|Found| B5{Owner or admin?}
        B5 -->|No| B6[403 Forbidden]
        B5 -->|Yes| B7{Action?}
        B7 -->|PATCH| B8[Apply changes]
        B8 --> B9[Return LessonResponse 200 OK]
        B7 -->|DELETE| B10[Delete lesson<br/>cascade: quiz + lesson_progress]
        B10 --> B11[Recalculate total_lessons in CourseProgress]
        B11 --> B12[Return 204 No Content]
    end

    classDef errorState   stroke:#f87171,fill:#fef2f2,color:#1e1b4b
    classDef successState stroke:#4ade80,fill:#f0fdf4,color:#1e1b4b
    classDef processState stroke:#38bdf8,fill:#f0f9ff,color:#1e1b4b
    classDef decisionState stroke:#fb923c,fill:#fff7ed,color:#1e1b4b

    class A4,A6,B4,B6 errorState
    class A9,B9,B12 successState
    class A1,A2,A7,A8,B1,B2,B8,B10,B11 processState
    class A3,A5,B3,B5,B7 decisionState
```

---

### F6 — Lesson Viewing & Auto-Completion

```mermaid
---
config:
  layout: elk
  theme: mc
---
flowchart TD
    subgraph VIEW["📖 View Lesson — GET /lessons/id"]
        A1[GET /lessons/id<br/>Student] --> A2[Fetch lesson]
        A2 --> A3{Found?}
        A3 -->|Not found| A4[404 Not Found]
        A3 -->|Found| A5[Check enrollment<br/>in lesson's course]
        A5 --> A6{Enrolled?}
        A6 -->|No| A7[403 Forbidden<br/>Not enrolled in this course]
        A6 -->|Yes| A8{Lesson has quiz?}
        A8 -->|Yes| A9[Return LessonResponse 200 OK<br/>no side effect]
        A8 -->|No| A10{lesson_progress<br/>already complete?}
        A10 -->|Yes| A11[Return LessonResponse 200 OK<br/>idempotent]
        A10 -->|No| A12[Mark lesson_progress.completed = true]
        A12 --> A13[ProgressService.recalculate<br/>student_id, course_id]
        A13 --> A14[Return LessonResponse 200 OK]
    end

    classDef errorState   stroke:#f87171,fill:#fef2f2,color:#1e1b4b
    classDef successState stroke:#4ade80,fill:#f0fdf4,color:#1e1b4b
    classDef processState stroke:#38bdf8,fill:#f0f9ff,color:#1e1b4b
    classDef decisionState stroke:#fb923c,fill:#fff7ed,color:#1e1b4b

    class A4,A7 errorState
    class A9,A11,A14 successState
    class A1,A2,A5,A12,A13 processState
    class A3,A6,A8,A10 decisionState
```

---

### F7 — Quiz & Question Management

```mermaid
---
config:
  layout: elk
  theme: mc
---
flowchart TD
    subgraph QUIZ["➕ Create Quiz — POST /lessons/lesson_id/quiz"]
        A1[POST /lessons/lesson_id/quiz<br/>title, passing_score=70] --> A2[Fetch lesson]
        A2 --> A3{Found?}
        A3 -->|Not found| A4[404 Not Found]
        A3 -->|Found| A5{Owner or admin?}
        A5 -->|No| A6[403 Forbidden]
        A5 -->|Yes| A7{Quiz already exists?}
        A7 -->|Yes| A8[409 ConflictError<br/>Quiz already exists for this lesson]
        A7 -->|No| A9[Create Quiz]
        A9 --> A10[Return QuizResponse 201 Created]
    end

    subgraph QUESTION["➕ Add Question — POST /quizzes/quiz_id/questions"]
        B1[POST /quizzes/quiz_id/questions<br/>text, question_type, options, order_index] --> B2[Fetch quiz + verify ownership]
        B2 --> B3{Question type valid?}
        B3 -->|single_choice: not exactly 1 correct| B4[422 Validation Error]
        B3 -->|multiple_choice: 0 correct options| B4
        B3 -->|Valid| B5[Create Question + AnswerOptions]
        B5 --> B6[Return QuestionResponse 201 Created]
    end

    subgraph STUDENT_VIEW["👁️ Student Views Quiz — GET /lessons/lesson_id/quiz"]
        C1[GET /lessons/lesson_id/quiz<br/>Student] --> C2[Fetch quiz + questions + options]
        C2 --> C3[Serialize with QuizDetailResponse]
        C3 --> C4[AnswerOptionResponse<br/>id + text only — is_correct hidden]
        C4 --> C5[Return QuizDetailResponse 200 OK]
    end

    classDef errorState   stroke:#f87171,fill:#fef2f2,color:#1e1b4b
    classDef successState stroke:#4ade80,fill:#f0fdf4,color:#1e1b4b
    classDef processState stroke:#38bdf8,fill:#f0f9ff,color:#1e1b4b
    classDef decisionState stroke:#fb923c,fill:#fff7ed,color:#1e1b4b

    class A4,A6,A8,B4 errorState
    class A10,B6,C5 successState
    class A1,A2,A9,B1,B2,B5,C1,C2,C3,C4 processState
    class A3,A5,A7,B3 decisionState
```

---

### F8 — Quiz Taking & Auto-grading

```mermaid
---
config:
  layout: elk
  theme: mc
---
flowchart TD
    subgraph SUBMIT["📝 Submit Quiz — POST /quizzes/quiz_id/submit"]
        A1[POST /quizzes/quiz_id/submit<br/>answers: question_id + selected_option_ids] --> A2[Fetch quiz]
        A2 --> A3{Found?}
        A3 -->|Not found| A4[404 Not Found]
        A3 -->|Found| A5[Check student enrolled<br/>in quiz's course]
        A5 --> A6{Enrolled?}
        A6 -->|No| A7[403 Forbidden]
        A6 -->|Yes| A8{Existing submission?}
        A8 -->|Yes| A9[409 ConflictError<br/>Already submitted]
        A8 -->|No| A10[Validate question_ids<br/>belong to this quiz]
        A10 --> A11{Valid?}
        A11 -->|No| A12[422 Validation Error]
        A11 -->|Yes| A13[AUTO-GRADE each question<br/>single_choice: selected == correct<br/>multiple_choice: selected set == correct set]
        A13 --> A14[score = correct_count / total × 100]
        A14 --> A15{score >= passing_score?}
        A15 -->|Yes| A16[passed = true]
        A15 -->|No| A17[passed = false]
        A16 --> A18[Save Submission + SubmissionAnswers]
        A17 --> A18
        A18 --> A19{Passed?}
        A19 -->|Yes| A20[Mark lesson_progress.completed = true]
        A20 --> A21[ProgressService.recalculate<br/>student_id, course_id]
        A21 --> A22[Return SubmissionDetailResponse 201 Created]
        A19 -->|No| A22
    end

    subgraph VIEW["🔎 View Submission — GET /quizzes/quiz_id/submission"]
        B1[GET /quizzes/quiz_id/submission<br/>Student] --> B2[Fetch submission<br/>for student_id + quiz_id]
        B2 --> B3{Found?}
        B3 -->|Not found| B4[404 Not Found<br/>No submission found]
        B3 -->|Found| B5[Return SubmissionDetailResponse 200 OK]
    end

    classDef errorState   stroke:#f87171,fill:#fef2f2,color:#1e1b4b
    classDef successState stroke:#4ade80,fill:#f0fdf4,color:#1e1b4b
    classDef processState stroke:#38bdf8,fill:#f0f9ff,color:#1e1b4b
    classDef decisionState stroke:#fb923c,fill:#fff7ed,color:#1e1b4b

    class A4,A7,A9,A12,B4 errorState
    class A22,B5 successState
    class A1,A2,A5,A10,A13,A14,A16,A17,A18,A20,A21,B1,B2 processState
    class A3,A6,A8,A11,A15,A19,B3 decisionState
```

---

### F9 — Progress Tracking

```mermaid
---
config:
  layout: elk
  theme: mc
---
flowchart TD
    subgraph COURSE["📊 View Course Progress — GET /courses/course_id/progress"]
        A1[GET /courses/course_id/progress<br/>Student] --> A2[Fetch CourseProgress<br/>for student + course]
        A2 --> A3{Found?}
        A3 -->|Not found| A4[404 Not Found<br/>Not enrolled or no progress record]
        A3 -->|Found| A5[Return CourseProgressResponse 200 OK]
    end

    subgraph RECALC["⚙️ Progress Recalculation — internal trigger"]
        B1[Trigger: ProgressService.recalculate<br/>student_id, course_id] --> B2[Count lesson_progress rows<br/>completed = true for student in course]
        B2 --> B3[Count total lessons in course]
        B3 --> B4[percent_complete = completed / total × 100]
        B4 --> B5{completed == total<br/>AND total > 0?}
        B5 -->|Yes| B6[is_complete = true]
        B5 -->|No| B7[is_complete = false]
        B6 --> B8[Upsert CourseProgress record]
        B7 --> B8
        B8 --> B9[Done]
    end

    subgraph ALL["📋 View All Progress — GET /progress"]
        C1[GET /progress<br/>Student] --> C2[Fetch all CourseProgress<br/>where student_id = current_user]
        C2 --> C3[Return CourseProgressListResponse 200 OK]
    end

    classDef errorState   stroke:#f87171,fill:#fef2f2,color:#1e1b4b
    classDef successState stroke:#4ade80,fill:#f0fdf4,color:#1e1b4b
    classDef processState stroke:#38bdf8,fill:#f0f9ff,color:#1e1b4b
    classDef decisionState stroke:#fb923c,fill:#fff7ed,color:#1e1b4b

    class A4 errorState
    class A5,B9,C3 successState
    class A1,A2,B1,B2,B3,B4,B6,B7,B8,C1,C2 processState
    class A3,B5 decisionState
```

---

### F10 — Admin Panel

```mermaid
---
config:
  layout: elk
  theme: mc
---
flowchart TD
    subgraph REST["🛠️ Admin REST Endpoints — /api/v1/admin/*"]
        A1[Request to<br/>/api/v1/admin/*] --> A2{role == admin?}
        A2 -->|No| A3[403 Forbidden<br/>Admin access required]
        A2 -->|Yes| A4{Endpoint?}
        A4 -->|GET /admin/users| A5[Paginated list of all users]
        A4 -->|GET /admin/users/id| A6[User detail]
        A4 -->|PATCH /admin/users/id| A7[Update role / is_active]
        A4 -->|DELETE /admin/users/id| A8[Delete user]
        A4 -->|GET /admin/courses| A9[Paginated list of all courses]
        A4 -->|PATCH /admin/courses/id| A10[Update any course]
        A4 -->|DELETE /admin/courses/id| A11[Delete any course]
        A4 -->|GET /admin/submissions| A12[Paginated list of all submissions]
        A4 -->|DELETE /admin/submissions/id| A13[Delete submission<br/>resets quiz attempt]
        A4 -->|GET /admin/progress| A14[Paginated list of all CourseProgress records]
    end

    subgraph UI["🖥️ SQLAdmin UI — GET /admin"]
        B1[Browser: GET /admin] --> B2{Authenticated<br/>as Admin?}
        B2 -->|No| B3[Redirect to /admin/login]
        B2 -->|Yes| B4[Render SQLAdmin dashboard]
        B4 --> B5[Entity tables<br/>Users / Courses / Lessons /<br/>Quizzes / Submissions / Progress]
    end

    classDef errorState   stroke:#f87171,fill:#fef2f2,color:#1e1b4b
    classDef successState stroke:#4ade80,fill:#f0fdf4,color:#1e1b4b
    classDef processState stroke:#38bdf8,fill:#f0f9ff,color:#1e1b4b
    classDef decisionState stroke:#fb923c,fill:#fff7ed,color:#1e1b4b

    class A3,B3 errorState
    class A5,A6,A7,A8,A9,A10,A11,A12,A13,A14,B5 successState
    class A1,B1,B4 processState
    class A2,A4,B2 decisionState
```

---

## Entity Relationship Diagram (ERD)

> **Legend**
> - `PK` — Primary Key (UUID)
> - `FK` — Foreign Key
> - `UNIQUE` — Unique constraint
> - `[]` — Array type (PostgreSQL `UUID[]`)

```mermaid
---
config:
  layout: elk
  theme: mc
---
erDiagram
    users {
        UUID id PK
        VARCHAR email "UNIQUE NOT NULL"
        VARCHAR username "UNIQUE NOT NULL"
        VARCHAR hashed_password "NOT NULL"
        VARCHAR full_name
        ENUM role "admin|instructor|student DEFAULT student"
        BOOLEAN is_active "DEFAULT true"
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    courses {
        UUID id PK
        VARCHAR title "NOT NULL"
        TEXT description
        UUID instructor_id FK
        BOOLEAN is_published "DEFAULT false"
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    enrollments {
        UUID id PK
        UUID student_id FK
        UUID course_id FK
        TIMESTAMP enrolled_at
    }

    lessons {
        UUID id PK
        UUID course_id FK
        VARCHAR title "NOT NULL"
        TEXT content "NOT NULL"
        INTEGER order_index "DEFAULT 0"
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    quizzes {
        UUID id PK
        UUID lesson_id FK "UNIQUE"
        VARCHAR title "NOT NULL"
        INTEGER passing_score "DEFAULT 70"
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    questions {
        UUID id PK
        UUID quiz_id FK
        TEXT text "NOT NULL"
        ENUM question_type "single_choice|multiple_choice"
        INTEGER order_index "DEFAULT 0"
    }

    answer_options {
        UUID id PK
        UUID question_id FK
        TEXT text "NOT NULL"
        BOOLEAN is_correct "DEFAULT false"
    }

    submissions {
        UUID id PK
        UUID student_id FK
        UUID quiz_id FK
        FLOAT score "0–100"
        BOOLEAN passed
        TIMESTAMP submitted_at
    }

    submission_answers {
        UUID id PK
        UUID submission_id FK
        UUID question_id FK
        UUID[] selected_option_ids "NOT NULL"
        BOOLEAN is_correct
    }

    lesson_progress {
        UUID id PK
        UUID student_id FK
        UUID lesson_id FK
        BOOLEAN completed "DEFAULT false"
        TIMESTAMP completed_at
    }

    course_progress {
        UUID id PK
        UUID student_id FK
        UUID course_id FK
        INTEGER completed_lessons "DEFAULT 0"
        INTEGER total_lessons
        FLOAT percent_complete "DEFAULT 0.0"
        BOOLEAN is_complete "DEFAULT false"
    }

    users ||--o{ courses : "instructs"
    users ||--o{ enrollments : "enrolls as student"
    courses ||--o{ enrollments : "has enrolled students"
    courses ||--o{ lessons : "contains"
    courses ||--o{ course_progress : "tracked by"
    lessons ||--o| quizzes : "has (optional)"
    lessons ||--o{ lesson_progress : "tracked by"
    quizzes ||--o{ questions : "contains"
    quizzes ||--o{ submissions : "receives"
    questions ||--o{ answer_options : "has"
    questions ||--o{ submission_answers : "answered in"
    users ||--o{ submissions : "submits"
    users ||--o{ lesson_progress : "has"
    users ||--o{ course_progress : "has"
    submissions ||--o{ submission_answers : "contains"
```

