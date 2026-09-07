"""adaptive strategy and content experiments

Revision ID: 0005_strategy
Revises: 0004_analytics
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_strategy"
down_revision = "0004_analytics"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "content_experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("variable", sa.String(64), nullable=False),
        sa.Column("control", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("variant", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="planned"),
        sa.Column("min_sample_size", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("winner", sa.String(32)),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("result", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_content_experiments_business", "content_experiments", ["business_id"])
    op.create_index("ix_content_experiments_status", "content_experiments", ["status"])

def downgrade() -> None:
    op.drop_table("content_experiments")
