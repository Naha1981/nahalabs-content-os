"""initial content os schema

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(120), nullable=False), sa.Column('plan_id', postgresql.UUID(as_uuid=True)), sa.Column('status', sa.String(32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index('ix_organizations_slug', 'organizations', ['slug'], unique=True)
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('cognito_sub', sa.String(255), nullable=False),
        sa.Column('email', sa.String(320), nullable=False), sa.Column('name', sa.String(200)), sa.Column('avatar_url', sa.String(1000)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index('ix_users_cognito_sub', 'users', ['cognito_sub'], unique=True); op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_table('memberships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False), sa.Column('role', sa.String(32), nullable=False),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_membership_org_user'))
    op.create_table('businesses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False), sa.Column('industry', sa.String(100)), sa.Column('description', sa.Text()), sa.Column('country', sa.String(100)), sa.Column('city', sa.String(100)),
        sa.Column('timezone', sa.String(64), nullable=False), sa.Column('website', sa.String(1000)), sa.Column('whatsapp', sa.String(40)), sa.Column('phone', sa.String(40)), sa.Column('email', sa.String(320)),
        sa.Column('status', sa.String(32), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index('ix_businesses_organization_id', 'businesses', ['organization_id'])
    op.create_table('brand_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tone', postgresql.JSONB(), nullable=False), sa.Column('audience', postgresql.JSONB(), nullable=False), sa.Column('visual_style', postgresql.JSONB(), nullable=False), sa.Column('brand_voice', postgresql.JSONB(), nullable=False),
        sa.Column('content_pillars', postgresql.JSONB(), nullable=False), sa.Column('language_preferences', postgresql.JSONB(), nullable=False), sa.Column('cta_preferences', postgresql.JSONB(), nullable=False),
        sa.Column('prohibited_topics', postgresql.JSONB(), nullable=False), sa.Column('brand_rules', postgresql.JSONB(), nullable=False), sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint('business_id'))
    op.create_table('media_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(32), nullable=False), sa.Column('storage_key', sa.String(1000), nullable=False), sa.Column('mime_type', sa.String(100), nullable=False), sa.Column('size_bytes', sa.Integer()),
        sa.Column('duration_ms', sa.Integer()), sa.Column('width', sa.Integer()), sa.Column('height', sa.Integer()), sa.Column('fps', sa.Float()), sa.Column('checksum', sa.String(128)), sa.Column('metadata', postgresql.JSONB(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index('ix_media_assets_business_id', 'media_assets', ['business_id']); op.create_index('ix_media_assets_storage_key', 'media_assets', ['storage_key'], unique=True)
    op.create_table('source_media',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('media_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('media_assets.id', ondelete='CASCADE'), nullable=False), sa.Column('status', sa.String(32), nullable=False), sa.Column('transcript', sa.Text()),
        sa.Column('scene_analysis', postgresql.JSONB(), nullable=False), sa.Column('object_analysis', postgresql.JSONB(), nullable=False), sa.Column('face_analysis', postgresql.JSONB(), nullable=False), sa.Column('audio_analysis', postgresql.JSONB(), nullable=False), sa.Column('content_summary', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint('media_asset_id'))
    op.create_index('ix_source_media_business_id', 'source_media', ['business_id'])
    op.create_table('content_packs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False), sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()), sa.Column('source_media_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('source_media.id', ondelete='SET NULL')), sa.Column('status', sa.String(32), nullable=False), sa.Column('asset_count', sa.Integer(), nullable=False),
        sa.Column('strategy', postgresql.JSONB(), nullable=False), sa.Column('generation_metadata', postgresql.JSONB(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index('ix_content_packs_business_id', 'content_packs', ['business_id'])
    op.create_table('generation_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content_pack_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('content_packs.id', ondelete='CASCADE')), sa.Column('job_type', sa.String(64), nullable=False), sa.Column('status', sa.String(32), nullable=False), sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False), sa.Column('last_error', sa.Text()), sa.Column('idempotency_key', sa.String(255)), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index('ix_generation_jobs_business_id', 'generation_jobs', ['business_id']); op.create_index('ix_generation_jobs_status', 'generation_jobs', ['status']); op.create_index('ix_generation_jobs_idempotency_key', 'generation_jobs', ['idempotency_key'], unique=True)
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')), sa.Column('action', sa.String(120), nullable=False), sa.Column('resource_type', sa.String(80), nullable=False), sa.Column('resource_id', sa.String(255), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=False), sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index('ix_audit_logs_organization_id', 'audit_logs', ['organization_id'])


def downgrade():
    for table in ['audit_logs','generation_jobs','content_packs','source_media','media_assets','brand_profiles','businesses','memberships','users','organizations']:
        op.drop_table(table)
