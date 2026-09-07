"""publishing and consent tables

Revision ID: 0003_publishing
Revises: 0002_generation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003_publishing'
down_revision = '0002_generation'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('zernio_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_profile_id', sa.String(255), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('business_id'), sa.UniqueConstraint('external_profile_id'))
    op.create_index('ix_zernio_profiles_business_id', 'zernio_profiles', ['business_id'])
    op.create_index('ix_zernio_profiles_external_profile_id', 'zernio_profiles', ['external_profile_id'])
    op.create_table('social_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(32), nullable=False, server_default='zernio'),
        sa.Column('platform', sa.String(32), nullable=False),
        sa.Column('external_profile_id', sa.String(255)),
        sa.Column('external_account_id', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255)), sa.Column('display_name', sa.String(255)),
        sa.Column('status', sa.String(32), nullable=False, server_default='connected'),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('disconnected_at', sa.DateTime(timezone=True)),
        sa.UniqueConstraint('business_id','provider','external_account_id', name='uq_social_account_external'))
    op.create_index('ix_social_accounts_business_id','social_accounts',['business_id'])
    op.create_index('ix_social_accounts_platform','social_accounts',['platform'])
    op.create_index('ix_social_accounts_status','social_accounts',['status'])
    op.create_table('approval_grants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('granted_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('scope', sa.String(32), nullable=False, server_default='batch'),
        sa.Column('allowed_platforms', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('allowed_content_types', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('expires_at', sa.DateTime(timezone=True)), sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index('ix_approval_grants_business_id','approval_grants',['business_id'])
    op.create_table('publishing_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('generated_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('generated_assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('social_account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('social_accounts.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('platform', sa.String(32), nullable=False), sa.Column('status', sa.String(32), nullable=False, server_default='draft'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True)), sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('external_post_id', sa.String(255)), sa.Column('attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text), sa.Column('payload', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('idempotency_key', sa.String(255), unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index('ix_publishing_jobs_business_id','publishing_jobs',['business_id'])
    op.create_index('ix_publishing_jobs_generated_asset_id','publishing_jobs',['generated_asset_id'])
    op.create_index('ix_publishing_jobs_social_account_id','publishing_jobs',['social_account_id'])
    op.create_index('ix_publishing_jobs_status','publishing_jobs',['status'])
    op.create_table('webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True), sa.Column('provider', sa.String(32), nullable=False),
        sa.Column('external_event_id', sa.String(255), nullable=False), sa.Column('event_type', sa.String(120)),
        sa.Column('payload', postgresql.JSONB, nullable=False, server_default='{}'), sa.Column('status', sa.String(32), nullable=False, server_default='received'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.UniqueConstraint('external_event_id'))
    op.create_index('ix_webhook_events_provider','webhook_events',['provider'])
    op.create_index('ix_webhook_events_external_event_id','webhook_events',['external_event_id'])
    op.create_index('ix_webhook_events_event_type','webhook_events',['event_type'])

def downgrade():
    op.drop_table('webhook_events'); op.drop_table('publishing_jobs'); op.drop_table('approval_grants'); op.drop_table('social_accounts'); op.drop_table('zernio_profiles')
