"""add loan due date

Revision ID: 9f2c4a1b7e30
Revises: 3b8e1f0c9a27
Create Date: 2026-01-04 10:12:00

"""

import sqlalchemy as sa
from alembic import op

revision: str = "9f2c4a1b7e30"
down_revision: str | None = "3b8e1f0c9a27"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("loan", sa.Column("due_on", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("loan", "due_on")


def describe_draft() -> str:
    # a local named revision is not a migration header
    revision: str = "draft-2"
    return revision
