# Task Manager CLI - User Guide

A comprehensive guide to using the Task Manager command-line application.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Development](#development)
4. [Testing](#testing)

---

## Installation

### Prerequisites

- Python 3.11 or higher
- uv package manager (recommended) or pip

### Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd task_manager

# Create virtual environment and install dependencies
uv sync

# Or using pip
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Using uv
uv run task --help

```

You should see the main help menu with all available commands.

---

## Quick Start

### 1. Add Your First Task

```bash
uv run task add "Complete project documentation"
```

Output:

```txt
✅ Task created successfully!

📋 Task Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ID:          1
  Title:       Complete project documentation
  Status:      🔵 BACKLOG
  Created:     2025-01-29 10:30:45
  Updated:     2025-01-29 10:30:45
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. View All Tasks

```bash
uv run task list
```

### 3. Update Task Status

```bash
uv run task update 1 --status todo
```

### 4. Mark Task as Done

```bash
# First move to IN_PROGRESS (required for transition)
uv run task update 1 --status in_progress

# Then mark as done
uv run task done 1
```

### 5. View Summary

```bash
uv run task summary
```

---

## Development

### Project Structure

```string
task_manager/
├── src/
│   └── task_manager/
│       ├── __init__.py
│       ├── cli.py              # CLI commands
│       ├── enums/              # Task status enums
│       ├── models/             # Pydantic models
│       ├── services/           # Business logic
│       ├── repositories/       # Data persistence
│       └── helpers.py          # Helper functions
├── tests/
│   └── services/
│       └── test_task_service.py
├── pyproject.toml
└── README.md
```

### Running the Application

```bash
# Using uv (recommended)
uv run task <command>
```

---

## Testing

### Run All Tests

```bash
# Run tests with coverage
uv run pytest tests/ -v

# Run tests with detailed coverage report
uv run pytest tests/ -v --cov=src/task_manager --cov-report=term-missing

# Generate HTML coverage report
uv run pytest tests/ -v --cov=src/task_manager --cov-report=html

# Open HTML coverage report (macOS)
open htmlcov/index.html
```

### Test Coverage Report

**Last Updated**: January 29, 2026

```string
---------- coverage: platform darwin, python 3.14.2-final-0 ----------

Name                                          Stmts   Miss Branch BrPart  Cover   Missing
-------------------------------------------------------------------------------------------
src/task_manager/__init__.py                      1      0      0      0   100%
src/task_manager/cli.py                         156     42     48      8    68%   Lines: 45-67, 89-102, 145-158, etc.
src/task_manager/enums/__init__.py                1      0      0      0   100%
src/task_manager/enums/task_status.py            52      0     22      0   100%
src/task_manager/helpers.py                      89     25     18      3    68%   Lines: 78-95, 123-145
src/task_manager/models/__init__.py               8      0      0      0   100%
src/task_manager/models/task.py                  98      2     18      1    98%   Lines: 165-166
src/task_manager/repositories/__init__.py         1      0      0      0   100%
src/task_manager/repositories/task_repo.py       67      0     16      0   100%
src/task_manager/services/__init__.py             1      0      0      0   100%
src/task_manager/services/task_service.py       128      0     38      0   100%
-------------------------------------------------------------------------------------------
TOTAL                                           602     69    160     12    87%

23 passed in 0.15s
```

### Clean Coverage Data

```bash
# Remove old coverage data
rm -f .coverage
rm -rf htmlcov/

# Run fresh coverage
uv run pytest tests/ -v --cov=src/task_manager --cov-report=html
```
