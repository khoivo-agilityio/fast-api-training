"""Structured logging setup using structlog.

Configures structlog with two output modes:
  - console  → coloured, human-readable (development)
  - json     → machine-readable JSON (production / staging)

Usage
-----
Call `setup_logging()` once at application startup (inside lifespan).

Then get a logger anywhere:
    import structlog
    logger = structlog.get_logger(__name__)
    logger.info("task_created", task_id=42, owner="alice")
"""

import logging
import sys

import structlog

from src.core.config import get_settings


def setup_logging() -> None:
    """Configure structlog + stdlib logging for the application."""
    settings = get_settings()

    # ── Shared processors (run for every log event) ──────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        # Add log level to every event dict
        structlog.stdlib.add_log_level,
        # Add logger name (module path)
        structlog.stdlib.add_logger_name,
        # Add ISO-8601 timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Extract exception info into the event dict
        structlog.processors.StackInfoRenderer(),
        structlog.processors.ExceptionRenderer(),
    ]

    # ── Output renderer: JSON (prod) vs coloured console (dev) ───────────────
    if settings.LOG_FORMAT == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # ── Configure structlog ───────────────────────────────────────────────────
    structlog.configure(
        processors=[
            # Filter out events below the configured log level
            structlog.stdlib.filter_by_level,
            *shared_processors,
            # Prepare the event dict for the stdlib handler
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ── Configure stdlib root logger (so uvicorn/sqlalchemy go through it) ───
    formatter = structlog.stdlib.ProcessorFormatter(
        # Processors run ONLY on stdlib log records passed through structlog
        foreign_pre_chain=shared_processors,
        processor=renderer,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    # Remove any pre-existing handlers (e.g. uvicorn default)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.LOG_LEVEL)

    # Quieten noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
