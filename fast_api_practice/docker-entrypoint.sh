#!/bin/bash
set -euo pipefail

echo "==> Running database migrations..."
python -m alembic upgrade head

echo "==> Starting application..."
# Use `python -m uvicorn` (not the venv script) to avoid broken shebangs
# in multi-stage Docker builds. Same reason as `python -m alembic` above.
exec python -m uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
