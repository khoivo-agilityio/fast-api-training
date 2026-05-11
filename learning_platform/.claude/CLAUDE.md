# CLAUDE.md — Learning Platform

Instructions for Claude Code (and other AI agents) working on this project.

## Architecture

This project uses a **module-by-feature** layout under `src/`.
See `.github/copilot-instructions.md` for the full architecture description.

## Key Conventions

1. **Class-based services:** All module services use a class pattern:
   ```python
   class AuthService:
       def __init__(self, db: AsyncSession) -> None:
           self._db = db
   ```
   Wired via `Depends()` in a `dependencies.py` factory function per module.

2. **CPU-bound operations:** bcrypt hash/verify and similar CPU-bound work
   must use `asyncio.get_running_loop().run_in_executor(None, ...)` to avoid
   blocking the event loop. Never use bare `async def` for CPU-bound code.

3. **Module docstrings:** Every module's `__init__.py` must contain a docstring
   explaining the module's purpose, key files, and why it exists as a separate
   module.

4. **Async everywhere:** All DB operations use `async/await`. All Redis
   operations use `async/await`.

5. **Exception handling:** Services raise domain exceptions from
   `<module>/exceptions.py`. Global handlers in `main.py` convert to JSON.
   Route handlers have **NO** `try/except`. Use `raise ... from None` in
   except clauses to distinguish domain errors from exception handling errors.

6. **No cross-module imports of internal helpers.** Modules talk to each other
   only via their `service.py` public methods.

7. **Tests:** Use `aiosqlite` in-memory DB — never real PostgreSQL. Mock Redis.
   Import all ORM models before `create_all` (gotchas.md #3).

8. **Docker:** Use `python -m uvicorn` and `python -m alembic` (never bare
   scripts — shebangs break in multi-stage builds).

## Gotchas

See `gotchas.md` in the project root for known issues and workarounds.

## Common Commands

```bash
uv run pytest tests/ --tb=short -q              # Run tests
uv run ruff check src/ tests/                    # Lint
uv run ruff format src/ tests/                   # Format
uv run pytest tests/ -v --cov=src --cov-report=term-missing  # Coverage
```
