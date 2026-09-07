"""content intelligence engine

Revision ID: 0007_content_intelligence
Revises: 0006_adaptive_strategy
"""
from alembic import op

revision = "0007_content_intelligence"
down_revision = "0006_adaptive_strategy"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # v1.3 persists intelligence decisions in existing ContentPack/CreativeBrief
    # JSONB strategy fields; no new tables are required.
    pass

def downgrade() -> None:
    pass
