"""Alembic environment configuration.

Loads the database URL from src.core.config so there is a single source
of truth.  Imports Base.metadata from our models so --autogenerate can
detect schema changes.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from src.core.config import settings
from src.infrastructure.database.models import Base  # noqa: F401 — registers all models

# ── Alembic Config object ────────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url with the value from our Settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is the MetaData object that autogenerate will diff against
target_metadata = Base.metadata


# ── Offline mode (generate SQL scripts without a live DB) ─────────────────────
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Generates SQL statements without connecting to the database.
    Useful for reviewing migration SQL before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (connect to DB and apply migrations) ──────────────────────────
def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
