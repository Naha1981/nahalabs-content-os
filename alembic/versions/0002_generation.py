"""generation briefs and assets
Revision ID: 0002_generation
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision='0002_generation'; down_revision='0001_initial'; branch_labels=None; depends_on=None

def upgrade():
    op.create_table('creative_briefs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('content_pack_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('content_packs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content_type', sa.String(64), nullable=False), sa.Column('objective', sa.String(255), nullable=False),
        sa.Column('angle', sa.String(255), nullable=False), sa.Column('hook', sa.Text(), nullable=False),
        sa.Column('audience', sa.Text()), sa.Column('cta', sa.Text()), sa.Column('platforms', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('duration_seconds', sa.Integer()), sa.Column('visual_direction', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('copy_direction', postgresql.JSONB(), nullable=False, server_default='{}'), sa.Column('status', sa.String(32), nullable=False, server_default='planned'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index('ix_creative_briefs_content_pack_id','creative_briefs',['content_pack_id'])
    op.create_table('generated_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('content_pack_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('content_packs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('creative_brief_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('creative_briefs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('media_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('media_assets.id', ondelete='SET NULL')),
        sa.Column('asset_type', sa.String(32), nullable=False), sa.Column('status', sa.String(32), nullable=False, server_default='queued'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'), sa.Column('generation_provider', sa.String(64)),
        sa.Column('generation_model', sa.String(128)), sa.Column('provider_job_id', sa.String(255)), sa.Column('generation_cost', sa.Float()),
        sa.Column('quality_score', sa.Float()), sa.Column('brand_score', sa.Float()), sa.Column('platform_score', sa.Float()),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('creative_brief_id','version',name='uq_generated_asset_brief_version'))
    op.create_index('ix_generated_assets_content_pack_id','generated_assets',['content_pack_id'])
    op.create_index('ix_generated_assets_creative_brief_id','generated_assets',['creative_brief_id'])

def downgrade():
    op.drop_table('generated_assets'); op.drop_table('creative_briefs')
