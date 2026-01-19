# Python CLI Task Manager

A professional, portfolio-ready **Python-based Command-Line Interface (CLI)** application for managing tasks, designed with **modern Python practices**, **strong typing**, and **QA-friendly testing**.

---

## 1. Project Goal

Build a maintainable, testable, and well-structured CLI application that allows users to manage tasks efficiently from the terminal.

This project demonstrates:

- Clean architecture & modular design
- Clear requirements thinking (BA mindset)
- Strong typing & validation
- Enterprise-style testing (QA mindset)
- Modern Python tooling

---

## 2. Functional Requirements

### FR-01: View All Tasks

- Display all tasks in a readable format
- Fields shown:

  - ID
  - Title
  - Status (BACKLOG / TODO / IN_PROGRESS / TESTING / DONE)
  - Created date
  - Updated date

- Show an empty-state message if no tasks exist

---

### FR-02: Add Task

- User can add a new task
- Inputs:

  - Title (required)
  - Description (optional)

**Acceptance Criteria**

- ID auto-generated
- Default status = `BACKLOG`
- Created timestamp saved
- Validation error if title is empty

---

### FR-03: Remove Task

- User removes a task by ID

**Acceptance Criteria**

- Task deleted if ID exists
- Error message if ID not found
- Confirmation message displayed

---

### FR-04: Update Task / Mark as Done

- Update task title or mark task as completed

**Acceptance Criteria**

- Status transitions across workflow states (e.g. `BACKLOG → TODO → IN_PROGRESS → TESTING → DONE`)
- Updated timestamp refreshed
- Cannot re-complete an already completed task
- Error if task ID does not exist

---

### FR-05: Filter Tasks by Status

- Filter tasks by status

\*\*Supported Filters

- `--status backlog`
- `--status todo`
- `--status in-progress`
- `--status testing`
- `--status done`

**Acceptance Criteria**

- Case-insensitive filtering
- Empty-result message when no tasks match

---

### FR-06: Summary

- Display task summary:

  - Total tasks
  - Pending count
  - Done count
  - Completion percentage (DONE / total tasks)

---

### FR-07: Export / Report (Optional)

- Export tasks to a file

**Formats**

- JSON (required)
- CSV (optional)

**Acceptance Criteria**

- File generated successfully
- Correct schema and values
- Output path displayed to user

---

## 3. Non-Functional Requirements

### Usability

- Simple, consistent CLI commands
- `--help` available for all commands

### Performance

- < 100ms response time for ≤ 10,000 tasks

### Maintainability

- Modular structure
- Clear separation of concerns
- Fully typed public interfaces

---

## 4. CLI Command Design

```bash
task add "Write unit tests"
task list
task list --status pending
task done 3
task remove 2
task summary
task export --format json
```

---

## 5. Tech Stack (Finalized)

### CLI Framework

- **Typer** (recommended)

  - Built on Click
  - Type-hint first
  - Automatic help generation

Alternative:

- **Click** – more explicit, lower magic

---

### Data Modeling & Validation

- **Pydantic (v2)**

  - Strong typing
  - Runtime validation
  - Serialization/deserialization for storage & export
  - Enum validation for task status workflow

---

### Testing

- **unittest** (standard library)
- **unittest.mock** for isolation

**Testing Layers**

- Unit tests: services, models, validators
- Integration tests: CLI + repository

---

### Linting & Formatting

- **ruff**

  - Linting
  - Formatting (Black replacement)
  - Import sorting

Recommended rules:

- E, F – correctness
- I – imports
- UP – modern Python
- ANN – typing discipline
- B – bugbear
- SIM – simplifications

---

### Git Hooks

- **pre-commit**

  - Enforce linting & formatting before commit

---

### Python Environment Management

- **uv**

  - Virtual environments
  - Dependency management
  - Fast replacement for pip + venv

---

## 6. Project Folder Structure

```text
task_manager/
├── pyproject.toml
├── README.md
├── .gitignore
├── .pre-commit-config.yaml
│
├── src/
│   └── task_manager/
│       ├── __init__.py
│
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py          # Typer / Click app
│
│       ├── models/
│       │   ├── __init__.py
│       │   ├── task.py          # Pydantic Task model
│       │   └── enums.py         # TaskStatus (Backlog, Todo, InProgress, Testing, Done)
│
│       ├── services/
│       │   ├── __init__.py
│       │   └── task_service.py  # Business logic
│
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── base.py          # Repository protocol
│       │   └── json_repo.py
│
│       ├── reporting/
│       │   ├── __init__.py
│       │   ├── summary.py
│       │   └── export.py
│
│       └── utils/
│           ├── __init__.py
│           └── time.py
│
├── tests/
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_storage.py
│   ├── test_cli.py
│   └── test_reporting.py
│
└── scripts/
    └── run_dev.sh
```

---

## 7. Tooling Configuration (Reference)

### pyproject.toml (Minimal)

```toml
[project]
name = "task-manager"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "typer",
  "pydantic",
]

[project.scripts]
task = "task_manager.cli.main:app"

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "UP", "B", "SIM", "ANN"]
ignore = ["ANN101"]

[tool.ruff.format]
quote-style = "double"
```

---

### pre-commit

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.14
    hooks:
      - id: ruff
      - id: ruff-format
```

---

## 8. Development Workflow

1. Finalize requirements
2. Write failing tests (TDD-lite)
3. Implement core business logic
4. Add CLI layer
5. Apply linting & formatting
6. Add export/reporting
7. Polish README & examples
