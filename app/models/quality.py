from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, Float, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class QualityCheck(Base):
    __tablename__ = 'quality_checks'
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    generated_asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('generated_assets.id', ondelete='CASCADE'), index=True)
    status: Mapped[str] = mapped_column(String(32), default='passed', index=True)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    technical_score: Mapped[float] = mapped_column(Float, default=0.0)
    visual_score: Mapped[float] = mapped_column(Float, default=0.0)
    brand_score: Mapped[float] = mapped_column(Float, default=0.0)
    platform_score: Mapped[float] = mapped_column(Float, default=0.0)
    safety_score: Mapped[float] = mapped_column(Float, default=1.0)
    issues: Mapped[list] = mapped_column(JSONB, default=list)
    warnings: Mapped[list] = mapped_column(JSONB, default=list)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
