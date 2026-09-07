from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import ContentInsight, PostMetric, PublishingJob


def value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def metrics_from_row(row: dict) -> dict:
    keys = ("impressions", "reach", "views", "likes", "comments", "shares", "saves", "clicks", "follows")
    out = {k: int(value(row, k, 0) or 0) for k in keys}
    denominator = max(out["impressions"], out["reach"], out["views"], 1)
    interactions = out["likes"] + out["comments"] + out["shares"] + out["saves"] + out["clicks"]
    out["engagement_rate"] = interactions / denominator
    return out


async def ingest_post_analytics(db: AsyncSession, business_id, rows: list[dict]) -> int:
    jobs = (await db.execute(select(PublishingJob).where(PublishingJob.business_id == business_id))).scalars().all()
    by_external = {j.external_post_id: j for j in jobs if j.external_post_id}
    inserted = 0
    for row in rows:
        external = value(row, "id") or value(row, "postId") or value(row, "platformPostId")
        job = by_external.get(str(external))
        if not job:
            continue
        metrics = metrics_from_row(row)
        captured = datetime.now(timezone.utc).replace(microsecond=0)
        exists = await db.scalar(select(PostMetric.id).where(PostMetric.publishing_job_id == job.id, PostMetric.captured_at == captured))
        if exists:
            continue
        db.add(PostMetric(
            publishing_job_id=job.id,
            platform=value(row, "platform", job.platform),
            platform_post_id=str(value(row, "platformPostId", external)) if external else None,
            **metrics,
            captured_at=captured,
            raw=row if isinstance(row, dict) else {},
        ))
        inserted += 1
    await db.commit()
    return inserted


async def refresh_insights(db: AsyncSession, business_id) -> list[ContentInsight]:
    rows = (await db.execute(select(PostMetric, PublishingJob).join(PublishingJob, PublishingJob.id == PostMetric.publishing_job_id).where(PublishingJob.business_id == business_id))).all()
    if not rows:
        return []
    by_platform = defaultdict(list)
    for metric, job in rows:
        by_platform[job.platform].append(metric)
    created = []
    await db.execute(delete(ContentInsight).where(ContentInsight.business_id == business_id))
    for platform, metrics in by_platform.items():
        best = max(metrics, key=lambda m: m.engagement_rate)
        created.append(ContentInsight(
            business_id=business_id,
            insight_type="platform_performance",
            insight=f"{platform} is currently the strongest measured platform by engagement rate.",
            evidence={"platform": platform, "engagement_rate": best.engagement_rate, "views": best.views, "likes": best.likes, "shares": best.shares},
            confidence=min(1.0, len(metrics) / 10),
        ))
    global_best = max(rows, key=lambda pair: pair[0].engagement_rate)
    metric, job = global_best
    created.append(ContentInsight(
        business_id=business_id,
        insight_type="winning_content",
        insight="The highest-engagement published asset should influence the next creative batch.",
        evidence={"publishing_job_id": str(job.id), "platform": job.platform, "engagement_rate": metric.engagement_rate, "views": metric.views, "shares": metric.shares, "clicks": metric.clicks},
        confidence=min(1.0, len(rows) / 20),
    ))
    db.add_all(created)
    await db.commit()
    return created
