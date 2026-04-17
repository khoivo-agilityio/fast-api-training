# ============================================================
# Stage 1: Builder — install Python dependencies
# ============================================================
FROM python:3.14-slim AS builder

# Prevents Python from writing .pyc files and enables unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install system deps needed to compile async drivers (asyncpg, bcrypt)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency manifests first (layer caching)
COPY pyproject.toml uv.lock ./

# Install production dependencies into a virtual environment.
# UV_PYTHON_PREFERENCE=only-system forces uv to use the image's own Python
# instead of downloading a separate interpreter into /root/.local/…
RUN UV_PYTHON_PREFERENCE=only-system uv sync --frozen --no-dev --no-install-project

# Copy application source
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# ============================================================
# Stage 2: Runtime — minimal image
# ============================================================
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Tell Python where the venv lives
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Runtime system deps only (no compiler)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

# Copy virtual environment and source from builder
COPY --from=builder --chown=appuser:appuser /build/.venv ./.venv
COPY --from=builder --chown=appuser:appuser /build/src ./src
COPY --from=builder --chown=appuser:appuser /build/alembic ./alembic
COPY --from=builder --chown=appuser:appuser /build/alembic.ini ./

# Copy entrypoint
COPY --chown=appuser:appuser docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
