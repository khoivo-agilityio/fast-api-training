"""Background task functions for email notifications.

When ``SMTP_ENABLED=true`` in the environment, real emails are delivered via
the configured SMTP server (SSL on port 465 by default).  When the flag is
false (the default for development / tests) the functions only emit a structlog
entry — no network I/O, no credentials required.

All functions are plain sync callables so FastAPI ``BackgroundTasks`` runs them
in a thread pool, keeping the async event-loop free.

Logging
-------
Every public task function is wrapped with ``@_log_task``.  On each run the
decorator emits two structured log events:

* ``background_task_started``  — task name + keyword arguments
* ``background_task_finished`` — task name + wall-clock duration (ms)

On an unhandled exception it emits:

* ``background_task_failed``   — task name + duration + exc_info
"""

import functools
import smtplib
import ssl
import time
from collections.abc import Callable
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import certifi
import structlog

from src.core.config import get_settings

logger = structlog.get_logger(__name__)


# ── logging decorator ─────────────────────────────────────────────────────────


def _log_task[F: Callable[..., None]](fn: F) -> F:
    """Wrap a background-task function with structured start/finish/fail logs.

    Usage::

        @_log_task
        def my_task(foo: str, bar: int) -> None:
            ...
    """

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        task_name = fn.__name__
        log = logger.bind(task=task_name)

        log.info("background_task_started", kwargs=kwargs)
        start = time.perf_counter()
        try:
            fn(*args, **kwargs)
            duration_ms = round((time.perf_counter() - start) * 1_000, 2)
            log.info("background_task_finished", duration_ms=duration_ms)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1_000, 2)
            log.exception("background_task_failed", duration_ms=duration_ms)
            raise

    return wrapper  # type: ignore[return-value]  # inner wrapper preserves signature via functools.wraps


# ── internal SMTP helper ──────────────────────────────────────────────────────


def _send_email(
    *,
    to: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
) -> None:
    """Send an email via the configured SMTP server.

    Falls back to a debug log when ``SMTP_ENABLED`` is false so the rest of
    the app works without any mail configuration in development / CI.
    """
    settings = get_settings()

    if not settings.SMTP_ENABLED:
        logger.debug(
            "email_skipped",
            reason="SMTP_ENABLED=false",
            to=to,
            subject=subject,
        )
        return

    sender = settings.SMTP_FROM or settings.SMTP_USERNAME

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    msg.attach(MIMEText(body_text, "plain"))
    if body_html:
        msg.attach(MIMEText(body_html, "html"))

    context = ssl.create_default_context(cafile=certifi.where())
    try:
        if settings.SMTP_PORT == 587:
            with smtplib.SMTP(
                settings.SMTP_HOST, settings.SMTP_PORT, timeout=10
            ) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(sender, to, msg.as_string())
        else:
            with smtplib.SMTP_SSL(
                settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=10
            ) as server:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(sender, to, msg.as_string())

        logger.info("email_delivered", to=to, subject=subject)
    except smtplib.SMTPException:
        logger.exception("email_failed", to=to, subject=subject)
        raise


@_log_task
def simulate_task_assignment_email(
    task_id: int,
    task_title: str,
    assignee_id: int,
    project_id: int,
) -> None:
    """Send (or log) an email when a task is assigned to a user.

    To deliver a real email here you need the assignee's address. Fetch it in
    the calling route and add an ``assignee_email`` parameter when ready.
    """
    logger.info(
        "email_sent",
        email_type="task_assigned",
        task_id=task_id,
        task_title=task_title,
        assignee_id=assignee_id,
        project_id=project_id,
        message=(
            f"Simulated email: Task '{task_title}' (ID={task_id}) "
            f"assigned to user {assignee_id} in project {project_id}."
        ),
    )


@_log_task
def simulate_project_created_email(
    project_id: int,
    project_name: str,
    owner_id: int,
) -> None:
    """Send (or log) an email when a new project is created."""
    logger.info(
        "email_sent",
        email_type="project_created",
        project_id=project_id,
        project_name=project_name,
        owner_id=owner_id,
        message=(
            f"Simulated email: Project '{project_name}' (ID={project_id}) "
            f"created by user {owner_id}."
        ),
    )


@_log_task
def simulate_welcome_email(
    user_id: int,
    username: str,
    email: str,
) -> None:
    """Send a welcome email when a new user registers.

    Delivers a real email when ``SMTP_ENABLED=true``; logs only otherwise.
    """
    logger.info(
        "email_sent",
        email_type="welcome",
        user_id=user_id,
        username=username,
        email=email,
    )

    settings = get_settings()
    subject = f"Welcome to {settings.APP_NAME}, {username}!"
    body_text = (
        f"Hi {username},\n\n"
        f"Welcome to {settings.APP_NAME}! "
        "Your account has been created successfully.\n\n"
        "Get started by creating your first project.\n\n"
        "Cheers,\n"
        f"The {settings.APP_NAME} team"
    )
    body_html = (
        f"<html><body>"
        f"<h2>Welcome to {settings.APP_NAME}, {username}!</h2>"
        f"<p>Your account has been created successfully.</p>"
        f"<p>Get started by creating your first project.</p>"
        f"<br><p>Cheers,<br>The {settings.APP_NAME} team</p>"
        f"</body></html>"
    )

    _send_email(to=email, subject=subject, body_text=body_text, body_html=body_html)
