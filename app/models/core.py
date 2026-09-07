import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


def uuid_pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Organization(Base):
    __tablename__ = 'organizations'
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = 'users'
    id: Mapped[uuid.UUID] = uuid_pk()
    cognito_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(200))
    avatar_url: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Membership(Base):
    __tablename__ = 'memberships'
    __table_args__ = (UniqueConstraint('organization_id', 'user_id', name='uq_membership_org_user'),)
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    role: Mapped[str] = mapped_column(String(32), default='viewer')


class Business(Base):
    __tablename__ = 'businesses'
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(64), default='Africa/Johannesburg')
    website: Mapped[str | None] = mapped_column(String(1000))
    whatsapp: Mapped[str | None] = mapped_column(String(40))
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(320))
    status: Mapped[str] = mapped_column(String(32), default='active')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BrandProfile(Base):
    __tablename__ = 'brand_profiles'
    id: Mapped[uuid.UUID] = uuid_pk()
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('businesses.id', ondelete='CASCADE'), unique=True)
    tone: Mapped[dict] = mapped_column(JSONB, default=dict)
    audience: Mapped[dict] = mapped_column(JSONB, default=dict)
    visual_style: Mapped[dict] = mapped_column(JSONB, default=dict)
    brand_voice: Mapped[dict] = mapped_column(JSONB, default=dict)
    content_pillars: Mapped[list] = mapped_column(JSONB, default=list)
    language_preferences: Mapped[list] = mapped_column(JSONB, default=list)
    cta_preferences: Mapped[list] = mapped_column(JSONB, default=list)
    prohibited_topics: Mapped[list] = mapped_column(JSONB, default=list)
    brand_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MediaAsset(Base):
    __tablename__ = 'media_assets'
    id: Mapped[uuid.UUID] = uuid_pk()
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('businesses.id', ondelete='CASCADE'), index=True)
    type: Mapped[str] = mapped_column(String(32))
    storage_key: Mapped[str] = mapped_column(String(1000), unique=True)
    mime_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    fps: Mapped[float | None]
    checksum: Mapped[str | None] = mapped_column(String(128))
    asset_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SourceMedia(Base):
    __tablename__ = 'source_media'
    id: Mapped[uuid.UUID] = uuid_pk()
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('businesses.id', ondelete='CASCADE'), index=True)
    media_asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('media_assets.id', ondelete='CASCADE'), unique=True)
    status: Mapped[str] = mapped_column(String(32), default='uploaded')
    transcript: Mapped[str | None] = mapped_column(Text)
    scene_analysis: Mapped[dict] = mapped_column(JSONB, default=dict)
    object_analysis: Mapped[dict] = mapped_column(JSONB, default=dict)
    face_analysis: Mapped[dict] = mapped_column(JSONB, default=dict)
    audio_analysis: Mapped[dict] = mapped_column(JSONB, default=dict)
    content_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContentPack(Base):
    __tablename__ = 'content_packs'
    id: Mapped[uuid.UUID] = uuid_pk()
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('businesses.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    source_media_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('source_media.id', ondelete='SET NULL'))
    status: Mapped[str] = mapped_column(String(32), default='draft')
    asset_count: Mapped[int] = mapped_column(Integer, default=0)
    strategy: Mapped[dict] = mapped_column(JSONB, default=dict)
    generation_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class GenerationJob(Base):
    __tablename__ = 'generation_jobs'
    id: Mapped[uuid.UUID] = uuid_pk()
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('businesses.id', ondelete='CASCADE'), index=True)
    content_pack_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('content_packs.id', ondelete='CASCADE'))
    job_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default='queued', index=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), index=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    action: Mapped[str] = mapped_column(String(120))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(255))
    job_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
