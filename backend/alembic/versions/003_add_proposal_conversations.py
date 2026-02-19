"""Add proposal_conversations table for chat history

Revision ID: 003
Revises: 002
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create message_role enum
    op.execute("CREATE TYPE message_role AS ENUM ('user', 'assistant')")

    # Create proposal_conversations table
    op.create_table(
        "proposal_conversations",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "proposal_id",
            UUID(as_uuid=True),
            sa.ForeignKey("improvement_proposals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Convert role column to enum type
    op.execute(
        "ALTER TABLE proposal_conversations "
        "ALTER COLUMN role TYPE message_role USING role::message_role"
    )


def downgrade() -> None:
    op.drop_table("proposal_conversations")
    op.execute("DROP TYPE IF EXISTS message_role")
