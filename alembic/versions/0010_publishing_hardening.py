"""publishing hardening

Revision ID: 0010_publishing_hardening
Revises: 0009_publishing_preflight
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0010_publishing_hardening"
down_revision = "0009_publishing_preflight"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("publishing_jobs", sa.Column("provider_status", sa.String(length=64), nullable=True))
    op.add_column("publishing_jobs", sa.Column("provider_payload", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("publishing_jobs", sa.Column("provider_synced_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("publishing_jobs", sa.Column("reconciliation_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("ix_publishing_jobs_provider_status", "publishing_jobs", ["provider_status"])

def downgrade():
    op.drop_index("ix_publishing_jobs_provider_status", table_name="publishing_jobs")
    op.drop_column("publishing_jobs", "reconciliation_attempts")
    op.drop_column("publishing_jobs", "provider_synced_at")
    op.drop_column("publishing_jobs", "provider_payload")
    op.drop_column("publishing_jobs", "provider_status")
