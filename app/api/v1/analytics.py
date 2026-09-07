from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ContentInsight, PostMetric, PublishingJob

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/businesses/{business_id}/insights")
async def get_insights(business_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    rows = (await db.execute(select(ContentInsight).where(ContentInsight.business_id == business_id).order_by(ContentInsight.created_at.desc()))).scalars().all()
    return [{"id": str(x.id), "type": x.insight_type, "insight": x.insight, "evidence": x.evidence, "confidence": x.confidence} for x in rows]

@router.get("/businesses/{business_id}/posts")
async def get_post_metrics(business_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    rows = (await db.execute(select(PostMetric, PublishingJob).join(PublishingJob, PublishingJob.id == PostMetric.publishing_job_id).where(PublishingJob.business_id == business_id).order_by(PostMetric.captured_at.desc()).limit(200))).all()
    return [{"job_id": str(job.id), "platform": m.platform, "captured_at": m.captured_at, "impressions": m.impressions, "reach": m.reach, "views": m.views, "likes": m.likes, "comments": m.comments, "shares": m.shares, "saves": m.saves, "clicks": m.clicks, "follows": m.follows, "engagement_rate": m.engagement_rate} for m, job in rows]
