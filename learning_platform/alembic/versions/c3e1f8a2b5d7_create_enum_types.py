"""create progressstatus and questiontype enum types

Revision ID: c3e1f8a2b5d7
Revises: b1a12cb3f071
Create Date: 2026-05-24 19:18:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c3e1f8a2b5d7'
down_revision: Union[str, None] = 'b1a12cb3f071'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE progressstatus AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED')")
    op.execute("CREATE TYPE questiontype AS ENUM ('MCQ', 'TEXT')")


def downgrade() -> None:
    op.execute("DROP TYPE questiontype")
    op.execute("DROP TYPE progressstatus")
