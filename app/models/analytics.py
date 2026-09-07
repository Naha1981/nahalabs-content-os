from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Float, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


def pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class PostMetric(Base):
    __tablename__ = "post_metrics"
    __table_args__ = (UniqueConstraint("publishing_job_id", "captured_at", name="uq_post_metric_snapshot"),)
    id: Mapped[uuid.UUID] = pk()
    publishing_job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("publishing_jobs.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(32), index=True)
    platform_post_id: Mapped[str | None] = mapped_column(String(255), index=True)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    follows: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    raw: Mapped[dict] = mapped_column(JSONB, default=dict)

class ContentInsight(Base):
    __tablename__ = "content_insights"
    id: Mapped[uuid.UUID] = pk()
    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    insight_type: Mapped[str] = mapped_column(String(64), index=True)
    insight: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
