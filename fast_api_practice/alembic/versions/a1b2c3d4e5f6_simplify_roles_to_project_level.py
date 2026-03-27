"""simplify roles to project-level RBAC

- user_role_enum: admin/manager/member → user
- project_member_role_enum: manager/member → admin/member

Revision ID: a1b2c3d4e5f6
Revises: 120e14d02e4d
Create Date: 2026-03-27 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "120e14d02e4d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # ── 1. Simplify user_role_enum → only "user" ─────────────────────────────
    # Rename old enum, create new one, alter column casting all values to 'user'
    op.execute("ALTER TYPE user_role_enum RENAME TO user_role_enum_old")
    op.execute("CREATE TYPE user_role_enum AS ENUM ('user')")
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE user_role_enum "
        "USING 'user'::user_role_enum"
    )
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'user'")
    op.execute("DROP TYPE user_role_enum_old")

    # ── 2. Change project_member_role_enum: manager → admin ──────────────────
    # Rename old enum, create new one with admin/member, cast manager→admin
    op.execute(
        "ALTER TYPE project_member_role_enum RENAME TO project_member_role_enum_old"
    )
    op.execute("CREATE TYPE project_member_role_enum AS ENUM ('admin', 'member')")
    op.execute(
        "ALTER TABLE project_members ALTER COLUMN role "
        "TYPE project_member_role_enum "
        "USING (CASE WHEN role::text = 'manager' THEN 'admin' "
        "ELSE role::text END)::project_member_role_enum"
    )
    op.execute("DROP TYPE project_member_role_enum_old")


def downgrade() -> None:
    """Downgrade schema."""
    # ── Revert project_member_role_enum: admin → manager ─────────────────────
    op.execute("UPDATE project_members SET role = 'manager' WHERE role = 'admin'")
    op.execute(
        "ALTER TYPE project_member_role_enum RENAME TO project_member_role_enum_old"
    )
    op.execute("CREATE TYPE project_member_role_enum AS ENUM ('manager', 'member')")
    op.execute(
        "ALTER TABLE project_members ALTER COLUMN role "
        "TYPE project_member_role_enum "
        "USING role::text::project_member_role_enum"
    )
    op.execute("DROP TYPE project_member_role_enum_old")

    # ── Revert user_role_enum: user → admin/manager/member ───────────────────
    op.execute("ALTER TYPE user_role_enum RENAME TO user_role_enum_old")
    op.execute("CREATE TYPE user_role_enum AS ENUM ('admin', 'manager', 'member')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE user_role_enum "
        "USING 'member'::user_role_enum"
    )
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'member'")
    op.execute("DROP TYPE user_role_enum_old")
