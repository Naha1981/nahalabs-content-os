from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

def pk(): return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class CreativeBrief(Base):
    __tablename__ = 'creative_briefs'
    id: Mapped[uuid.UUID] = pk()
    content_pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('content_packs.id', ondelete='CASCADE'), index=True)
    content_type: Mapped[str] = mapped_column(String(64))
    objective: Mapped[str] = mapped_column(String(255))
    angle: Mapped[str] = mapped_column(String(255))
    hook: Mapped[str] = mapped_column(Text)
    audience: Mapped[str | None] = mapped_column(Text)
    cta: Mapped[str | None] = mapped_column(Text)
    platforms: Mapped[list] = mapped_column(JSONB, default=list)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    visual_direction: Mapped[dict] = mapped_column(JSONB, default=dict)
    copy_direction: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default='planned')
    strategy_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class GeneratedAsset(Base):
    __tablename__ = 'generated_assets'
    __table_args__ = (UniqueConstraint('creative_brief_id', 'version', name='uq_generated_asset_brief_version'),)
    id: Mapped[uuid.UUID] = pk()
    content_pack_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('content_packs.id', ondelete='CASCADE'), index=True)
    creative_brief_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('creative_briefs.id', ondelete='CASCADE'), index=True)
    media_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey('media_assets.id', ondelete='SET NULL'))
    asset_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default='queued')
    version: Mapped[int] = mapped_column(Integer, default=1)
    generation_provider: Mapped[str | None] = mapped_column(String(64))
    generation_model: Mapped[str | None] = mapped_column(String(128))
    provider_job_id: Mapped[str | None] = mapped_column(String(255))
    generation_cost: Mapped[float | None]
    quality_score: Mapped[float | None]
    brand_score: Mapped[float | None]
    platform_score: Mapped[float | None]
    asset_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
