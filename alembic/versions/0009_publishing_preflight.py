"""publishing preflight and explicit action approval

Revision ID: 0009_publishing_preflight
Revises: 0008_quality_engine
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0009_publishing_preflight'
down_revision = '0008_quality_engine'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('publishing_jobs', sa.Column('preflight_status', sa.String(length=32), nullable=False, server_default='pending'))
    op.add_column('publishing_jobs', sa.Column('preflight_result', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column('publishing_jobs', sa.Column('approved_by_user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('publishing_jobs', sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_publishing_jobs_preflight_status', 'publishing_jobs', ['preflight_status'])
    op.create_foreign_key('fk_publishing_jobs_approved_by_user', 'publishing_jobs', 'users', ['approved_by_user_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint('fk_publishing_jobs_approved_by_user', 'publishing_jobs', type_='foreignkey')
    op.drop_index('ix_publishing_jobs_preflight_status', table_name='publishing_jobs')
    op.drop_column('publishing_jobs', 'approved_at')
    op.drop_column('publishing_jobs', 'approved_by_user_id')
    op.drop_column('publishing_jobs', 'preflight_result')
    op.drop_column('publishing_jobs', 'preflight_status')
