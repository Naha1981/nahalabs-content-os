"""quality and approval gate

Revision ID: 0008_quality_engine
Revises: 0007_content_intelligence
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = '0008_quality_engine'
down_revision = '0007_content_intelligence'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'quality_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('generated_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('generated_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='passed'),
        sa.Column('overall_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('technical_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('visual_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('brand_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('platform_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('safety_score', sa.Float(), nullable=False, server_default='1'),
        sa.Column('issues', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('warnings', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('evidence', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_quality_checks_generated_asset_id', 'quality_checks', ['generated_asset_id'])
    op.create_index('ix_quality_checks_status', 'quality_checks', ['status'])

def downgrade():
    op.drop_table('quality_checks')
