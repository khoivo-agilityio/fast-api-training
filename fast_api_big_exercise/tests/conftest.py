"""Root conftest.py — re-exports all shared fixtures from tests/fixtures.py.

Pytest discovers fixtures defined (or imported) in conftest.py files and
makes them available to every test in the same directory and below.
By importing everything from fixtures.py here, every test file in the suite
can use any fixture without importing it manually.
"""

from tests.fixtures import (  # noqa: F401 — re-exported for pytest discovery
    auth_headers,
    auth_service,
    auth_token,
    client,
    create_test_tables,
    db_session,
    mock_task_repo,
    mock_user_repo,
    registered_user,
    task_service,
)
