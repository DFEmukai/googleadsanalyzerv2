"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ----------------------------------------------------------
    # 1. Create ENUM types via raw SQL to avoid driver issues
    # ----------------------------------------------------------
    op.execute("CREATE TYPE campaign_type_enum AS ENUM ('search', 'display', 'pmax', 'video')")
    op.execute("CREATE TYPE campaign_status_enum AS ENUM ('active', 'paused', 'ended')")
    op.execute("CREATE TYPE proposal_category_enum AS ENUM ('keyword', 'ad_copy', 'creative', 'targeting', 'budget', 'bidding', 'competitive_response')")
    op.execute("CREATE TYPE priority_enum AS ENUM ('high', 'medium', 'low')")
    op.execute("CREATE TYPE proposal_status_enum AS ENUM ('pending', 'approved', 'executed', 'rejected', 'skipped')")
    op.execute("CREATE TYPE insight_type_enum AS ENUM ('effective_pattern', 'ineffective_pattern', 'seasonal_trend', 'campaign_characteristic')")

    # ----------------------------------------------------------
    # 2. Create tables using sa.text() for ENUM column types
    #    to prevent SQLAlchemy from issuing CREATE TYPE again
    # ----------------------------------------------------------

    # campaigns
    op.create_table(
        "campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("campaign_id", sa.String, nullable=False, unique=True, index=True),
        sa.Column("campaign_name", sa.String, nullable=False),
        sa.Column("campaign_type", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("first_seen_at", sa.DateTime, nullable=False),
        sa.Column("last_seen_at", sa.DateTime, nullable=False),
        sa.Column("ended_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime,
                  server_default=sa.func.now(), nullable=False),
    )
    op.execute("ALTER TABLE campaigns ALTER COLUMN campaign_type TYPE campaign_type_enum USING campaign_type::campaign_type_enum")
    op.execute("ALTER TABLE campaigns ALTER COLUMN status TYPE campaign_status_enum USING status::campaign_status_enum")
    op.execute("ALTER TABLE campaigns ALTER COLUMN status SET DEFAULT 'active'")

    # competitors
    op.create_table(
        "competitors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("domain", sa.String, nullable=False),
        sa.Column("company_name", sa.String, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime,
                  server_default=sa.func.now(), nullable=False),
    )

    # weekly_reports
    op.create_table(
        "weekly_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("week_start_date", sa.Date, nullable=False),
        sa.Column("week_end_date", sa.Date, nullable=False),
        sa.Column("raw_data", JSONB, nullable=True),
        sa.Column("analysis_summary", sa.Text, nullable=True),
        sa.Column("kpi_snapshot", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime,
                  server_default=sa.func.now(), nullable=False),
    )

    # improvement_proposals
    op.create_table(
        "improvement_proposals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", UUID(as_uuid=True),
                  sa.ForeignKey("weekly_reports.id"), nullable=False),
        sa.Column("category", sa.String, nullable=False),
        sa.Column("priority", sa.String, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("expected_effect", sa.Text, nullable=True),
        sa.Column("action_steps", JSONB, nullable=True),
        sa.Column("target_campaign", sa.String, nullable=True),
        sa.Column("target_ad_group", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime,
                  server_default=sa.func.now(), nullable=False),
    )
    op.execute("ALTER TABLE improvement_proposals ALTER COLUMN category TYPE proposal_category_enum USING category::proposal_category_enum")
    op.execute("ALTER TABLE improvement_proposals ALTER COLUMN priority TYPE priority_enum USING priority::priority_enum")
    op.execute("ALTER TABLE improvement_proposals ALTER COLUMN status TYPE proposal_status_enum USING status::proposal_status_enum")
    op.execute("ALTER TABLE improvement_proposals ALTER COLUMN status SET DEFAULT 'pending'")

    # proposal_executions
    op.create_table(
        "proposal_executions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposal_id", UUID(as_uuid=True),
                  sa.ForeignKey("improvement_proposals.id"),
                  nullable=False, unique=True),
        sa.Column("executed_at", sa.DateTime, nullable=False),
        sa.Column("executed_by", sa.String, nullable=True),
        sa.Column("execution_notes", sa.Text, nullable=True),
        sa.Column("actual_changes", JSONB, nullable=True),
    )

    # proposal_results
    op.create_table(
        "proposal_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("proposal_id", UUID(as_uuid=True),
                  sa.ForeignKey("improvement_proposals.id"),
                  nullable=False, unique=True),
        sa.Column("measured_at", sa.DateTime, nullable=False),
        sa.Column("measurement_period", sa.String, nullable=True),
        sa.Column("before_metrics", JSONB, nullable=True),
        sa.Column("after_metrics", JSONB, nullable=True),
        sa.Column("effect_summary", sa.Text, nullable=True),
        sa.Column("effect_percentage", sa.Numeric(10, 2), nullable=True),
        sa.Column("ai_evaluation", sa.Text, nullable=True),
    )

    # learning_insights
    op.create_table(
        "learning_insights",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("insight_type", sa.String, nullable=False),
        sa.Column("category", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("evidence", JSONB, nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime,
                  server_default=sa.func.now(), nullable=False),
    )
    op.execute("ALTER TABLE learning_insights ALTER COLUMN insight_type TYPE insight_type_enum USING insight_type::insight_type_enum")

    # competitor_snapshots
    op.create_table(
        "competitor_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("competitor_id", UUID(as_uuid=True),
                  sa.ForeignKey("competitors.id"), nullable=False),
        sa.Column("captured_at", sa.DateTime, nullable=False),
        sa.Column("ad_copies", JSONB, nullable=True),
        sa.Column("keywords", JSONB, nullable=True),
        sa.Column("estimated_spend", sa.Numeric(12, 2), nullable=True),
        sa.Column("source", sa.Text, nullable=True),
    )

    # auction_insights
    op.create_table(
        "auction_insights",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("report_id", UUID(as_uuid=True),
                  sa.ForeignKey("weekly_reports.id"), nullable=False),
        sa.Column("competitor_domain", sa.String, nullable=False),
        sa.Column("impression_share", sa.Numeric(5, 4), nullable=True),
        sa.Column("overlap_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("position_above_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("top_of_page_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("outranking_share", sa.Numeric(5, 4), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("auction_insights")
    op.drop_table("competitor_snapshots")
    op.drop_table("learning_insights")
    op.drop_table("proposal_results")
    op.drop_table("proposal_executions")
    op.drop_table("improvement_proposals")
    op.drop_table("weekly_reports")
    op.drop_table("competitors")
    op.drop_table("campaigns")

    op.execute("DROP TYPE IF EXISTS insight_type_enum")
    op.execute("DROP TYPE IF EXISTS proposal_status_enum")
    op.execute("DROP TYPE IF EXISTS priority_enum")
    op.execute("DROP TYPE IF EXISTS proposal_category_enum")
    op.execute("DROP TYPE IF EXISTS campaign_status_enum")
    op.execute("DROP TYPE IF EXISTS campaign_type_enum")
