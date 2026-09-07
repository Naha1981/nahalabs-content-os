from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class ZernioProfile(Base):
    __tablename__ = 'zernio_profiles'
    id: Mapped[uuid.UUID] = pk()
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('businesses.id', ondelete='CASCADE'), unique=True, index=True)
    external_profile_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SocialAccount(Base):
    __tablename__ = 'social_accounts'
    __table_args__ = (UniqueConstraint('business_id', 'provider', 'external_account_id', name='uq_social_account_external'),)
    id: Mapped[uuid.UUID] = pk()
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('businesses.id', ondelete='CASCADE'), index=True)
    provider: Mapped[str] = mapped_column(String(32), default='zernio')
    platform: Mapped[str] = mapped_column(String(32), index=True)
    external_profile_id: Mapped[str | None] = mapped_column(String(255), index=True)
    external_account_id: Mapped[str] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default='connected', index=True)
    account_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class PublishingJob(Base):
    __tablename__ = 'publishing_jobs'
    id: Mapped[uuid.UUID] = pk()
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('businesses.id', ondelete='CASCADE'), index=True)
    generated_asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('generated_assets.id', ondelete='CASCADE'), index=True)
    social_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('social_accounts.id', ondelete='RESTRICT'), index=True)
    platform: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default='draft', index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_post_id: Mapped[str | None] = mapped_column(String(255), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    strategy_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    preflight_status: Mapped[str] = mapped_column(String(32), default='pending', index=True)
    preflight_result: Mapped[dict] = mapped_column(JSONB, default=dict)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True)
    provider_status: Mapped[str | None] = mapped_column(String(64), index=True)
    provider_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    provider_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reconciliation_attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ApprovalGrant(Base):
    __tablename__ = 'approval_grants'
    id: Mapped[uuid.UUID] = pk()
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('businesses.id', ondelete='CASCADE'), index=True)
    granted_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'))
    scope: Mapped[str] = mapped_column(String(32), default='batch')
    allowed_platforms: Mapped[list] = mapped_column(JSONB, default=list)
    allowed_content_types: Mapped[list] = mapped_column(JSONB, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class WebhookEvent(Base):
    __tablename__ = 'webhook_events'
    id: Mapped[uuid.UUID] = pk()
    provider: Mapped[str] = mapped_column(String(32), index=True)
    external_event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    event_type: Mapped[str | None] = mapped_column(String(120), index=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default='received')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
