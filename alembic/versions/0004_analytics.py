"""analytics and content insights

Revision ID: 0004_analytics
Revises: 0003_publishing
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_analytics"
down_revision = "0003_publishing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "post_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("publishing_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("publishing_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("platform_post_id", sa.String(255)),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reach", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shares", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("follows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engagement_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("raw", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_post_metrics_job", "post_metrics", ["publishing_job_id"])
    op.create_index("ix_post_metrics_platform", "post_metrics", ["platform"])
    op.create_index("ix_post_metrics_captured", "post_metrics", ["captured_at"])
    op.create_unique_constraint("uq_post_metric_snapshot", "post_metrics", ["publishing_job_id", "captured_at"])

    op.create_table(
        "content_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("insight_type", sa.String(64), nullable=False),
        sa.Column("insight", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_content_insights_business", "content_insights", ["business_id"])
    op.create_index("ix_content_insights_type", "content_insights", ["insight_type"])


def downgrade() -> None:
    op.drop_table("content_insights")
    op.drop_table("post_metrics")
