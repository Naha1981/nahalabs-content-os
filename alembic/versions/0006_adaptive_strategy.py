"""adaptive strategy decisions and experiment assignments

Revision ID: 0006_adaptive_strategy
Revises: 0005_strategy
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_adaptive_strategy"
down_revision = "0005_strategy"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("creative_briefs", sa.Column("strategy_metadata", postgresql.JSONB(), nullable=False, server_default="{}"))
    op.add_column("publishing_jobs", sa.Column("strategy_metadata", postgresql.JSONB(), nullable=False, server_default="{}"))
    op.create_index("ix_creative_briefs_strategy_metadata", "creative_briefs", ["strategy_metadata"], postgresql_using="gin")

def downgrade() -> None:
    op.drop_index("ix_creative_briefs_strategy_metadata", table_name="creative_briefs")
    op.drop_column("publishing_jobs", "strategy_metadata")
    op.drop_column("creative_briefs", "strategy_metadata")
