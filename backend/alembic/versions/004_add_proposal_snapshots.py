"""Add proposal_snapshots table for impact tracking

Revision ID: 004
Revises: 003
Create Date: 2026-02-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create snapshot_type enum
    op.execute("CREATE TYPE snapshot_type_enum AS ENUM ('before', 'after')")

    # Create proposal_snapshots table
    op.create_table(
        "proposal_snapshots",
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
        sa.Column("snapshot_type", sa.String, nullable=False),
        sa.Column("campaign_id", sa.String, nullable=True),
        # KPI metrics
        sa.Column("cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("conversions", sa.Numeric(10, 2), nullable=True),
        sa.Column("cpa", sa.Numeric(10, 2), nullable=True),
        sa.Column("ctr", sa.Numeric(8, 4), nullable=True),
        sa.Column("roas", sa.Numeric(10, 2), nullable=True),
        sa.Column("impressions", sa.Numeric(12, 0), nullable=True),
        sa.Column("clicks", sa.Numeric(12, 0), nullable=True),
        sa.Column("conversion_value", sa.Numeric(12, 2), nullable=True),
        # Period
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Convert snapshot_type column to enum type
    op.execute(
        "ALTER TABLE proposal_snapshots "
        "ALTER COLUMN snapshot_type TYPE snapshot_type_enum "
        "USING snapshot_type::snapshot_type_enum"
    )


def downgrade() -> None:
    op.drop_table("proposal_snapshots")
    op.execute("DROP TYPE IF EXISTS snapshot_type_enum")
