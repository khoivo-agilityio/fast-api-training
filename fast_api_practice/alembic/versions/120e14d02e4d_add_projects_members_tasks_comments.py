"""add projects members tasks comments

Revision ID: 120e14d02e4d
Revises: f70fd3aaf18c
Create Date: 2026-03-24 16:39:40.672265

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "120e14d02e4d"
down_revision: str | Sequence[str] | None = "f70fd3aaf18c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # ── comments ──────────────────────────────────────────────────────────────
    op.create_index(
        op.f("ix_comments_author_id"), "comments", ["author_id"], unique=False
    )
    op.drop_constraint(op.f("comments_task_id_fkey"), "comments", type_="foreignkey")
    op.drop_constraint(op.f("comments_author_id_fkey"), "comments", type_="foreignkey")
    op.create_foreign_key(
        "comments_task_id_fkey",
        "comments",
        "tasks",
        ["task_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "comments_author_id_fkey",
        "comments",
        "users",
        ["author_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── project_members ───────────────────────────────────────────────────────
    op.drop_constraint(op.f("uq_user_project"), "project_members", type_="unique")
    op.create_index(
        op.f("ix_project_members_project_id"),
        "project_members",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_members_user_id"),
        "project_members",
        ["user_id"],
        unique=False,
    )
    op.drop_constraint(
        op.f("project_members_user_id_fkey"),
        "project_members",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("project_members_project_id_fkey"),
        "project_members",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "project_members_user_id_fkey",
        "project_members",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "project_members_project_id_fkey",
        "project_members",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── projects ──────────────────────────────────────────────────────────────
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)
    op.create_index(
        op.f("ix_projects_owner_id"), "projects", ["owner_id"], unique=False
    )

    # ── tasks ─────────────────────────────────────────────────────────────────
    op.drop_index(op.f("ix_tasks_assignee_id"), table_name="tasks")
    op.create_index(op.f("ix_tasks_creator_id"), "tasks", ["creator_id"], unique=False)
    op.create_index(op.f("ix_tasks_title"), "tasks", ["title"], unique=False)
    op.drop_constraint(op.f("tasks_project_id_fkey"), "tasks", type_="foreignkey")
    op.drop_constraint(op.f("tasks_assignee_id_fkey"), "tasks", type_="foreignkey")
    op.drop_constraint(op.f("tasks_creator_id_fkey"), "tasks", type_="foreignkey")
    op.create_foreign_key(
        "tasks_project_id_fkey",
        "tasks",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "tasks_assignee_id_fkey",
        "tasks",
        "users",
        ["assignee_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "tasks_creator_id_fkey",
        "tasks",
        "users",
        ["creator_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # ── tasks ─────────────────────────────────────────────────────────────────
    op.drop_constraint("tasks_creator_id_fkey", "tasks", type_="foreignkey")
    op.drop_constraint("tasks_assignee_id_fkey", "tasks", type_="foreignkey")
    op.drop_constraint("tasks_project_id_fkey", "tasks", type_="foreignkey")
    op.create_foreign_key(
        op.f("tasks_creator_id_fkey"), "tasks", "users", ["creator_id"], ["id"]
    )
    op.create_foreign_key(
        op.f("tasks_assignee_id_fkey"),
        "tasks",
        "users",
        ["assignee_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("tasks_project_id_fkey"),
        "tasks",
        "projects",
        ["project_id"],
        ["id"],
    )
    op.drop_index(op.f("ix_tasks_title"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_creator_id"), table_name="tasks")
    op.create_index(
        op.f("ix_tasks_assignee_id"), "tasks", ["assignee_id"], unique=False
    )

    # ── projects ──────────────────────────────────────────────────────────────
    op.drop_index(op.f("ix_projects_owner_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")

    # ── project_members ───────────────────────────────────────────────────────
    op.drop_constraint(
        "project_members_project_id_fkey",
        "project_members",
        type_="foreignkey",
    )
    op.drop_constraint(
        "project_members_user_id_fkey",
        "project_members",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("project_members_project_id_fkey"),
        "project_members",
        "projects",
        ["project_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("project_members_user_id_fkey"),
        "project_members",
        "users",
        ["user_id"],
        ["id"],
    )
    op.drop_index(op.f("ix_project_members_user_id"), table_name="project_members")
    op.drop_index(op.f("ix_project_members_project_id"), table_name="project_members")
    op.create_unique_constraint(
        op.f("uq_user_project"),
        "project_members",
        ["user_id", "project_id"],
        postgresql_nulls_not_distinct=False,
    )

    # ── comments ──────────────────────────────────────────────────────────────
    op.drop_constraint("comments_author_id_fkey", "comments", type_="foreignkey")
    op.drop_constraint("comments_task_id_fkey", "comments", type_="foreignkey")
    op.create_foreign_key(
        op.f("comments_author_id_fkey"),
        "comments",
        "users",
        ["author_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("comments_task_id_fkey"),
        "comments",
        "tasks",
        ["task_id"],
        ["id"],
    )
    op.drop_index(op.f("ix_comments_author_id"), table_name="comments")
