"""Add manual_creative to proposal_category_enum

Revision ID: 002
Revises: 001
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE proposal_category_enum ADD VALUE IF NOT EXISTS 'manual_creative'"
    )


def downgrade() -> None:
    # PostgreSQL does not support removing enum values.
    # manual_creative will remain in the enum type.
    pass
