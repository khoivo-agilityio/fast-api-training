# Task Manager CLI - User Guide

A comprehensive guide to using the Task Manager command-line application.

---

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)

---

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd python-training

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .

# Typing Alias
alias task="python3 -m src.task_manager.cli"
```

### Verify Installation

```bash
task --help
```

You should see the main help menu with all available commands.

---

## Quick Start

### 1. Add Your First Task

```bash
task add "Complete project documentation"
```

Output:

```txt
✅ Task created successfully!

📋 Task Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ID:          1
  Title:       Complete project documentation
  Status:      🔵 BACKLOG
  Created:     2025-01-23 10:30:45
  Updated:     2025-01-23 10:30:45
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. View All Tasks

```bash
task list
```

### 3. Update Task Status

```bash
task update 1 --status todo
```

### 4. Mark Task as Done

```bash
task done 1
```

### 5. View Summary

```bash
task summary
```

---

## Getting Help

### Command Help

```bash
# General help
task --help

# Command-specific help
task add --help
task list --help
task update --help
```

### Common Commands Quick Reference

```bash
task add "Title"              # Add task
task list                     # List all
task list -s todo             # Filter by status
task show 1                   # Show details
task update 1 -s todo         # Update status
task done 1                   # Mark complete
task remove 1                 # Delete task
task summary                  # View stats
```
