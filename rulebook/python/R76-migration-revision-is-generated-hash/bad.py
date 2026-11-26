"""add loan due date

Revision ID: loans02duedate
Revises: 3b8e1f0c9a27, loans01init
Create Date: 2026-01-04 10:12:00

"""

import sqlalchemy as sa
from alembic import op

# mnemonic id that reads well in a filename but the tool never produced it
revision: str = "loans02duedate"  # expect: R76
# merge parent tuple mixing a real hash with a mnemonic, and the docstring names a different first parent
down_revision = ("4c1d2e3f4a5b", "loans01init")  # expect: R76  # expect-llm: R76
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("loan", sa.Column("due_on", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("loan", "due_on")
