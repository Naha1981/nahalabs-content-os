from __future__ import annotations
from collections import defaultdict
from statistics import mean
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import BrandProfile, Business, ContentInsight, CreativeBrief, GeneratedAsset, PostMetric, PublishingJob

MIN_POSTS_FOR_WINNER = 5

async def build_strategy_context(db: AsyncSession, business_id) -> dict:
    business = await db.get(Business, business_id)
    if not business:
        raise ValueError("Business not found")
    brand = await db.scalar(select(BrandProfile).where(BrandProfile.business_id == business_id))
    insights = (await db.execute(
        select(ContentInsight).where(ContentInsight.business_id == business_id)
        .order_by(ContentInsight.created_at.desc()).limit(50)
    )).scalars().all()
    rows = (await db.execute(
        select(PostMetric, PublishingJob, CreativeBrief)
        .join(PublishingJob, PublishingJob.id == PostMetric.publishing_job_id)
        .join(GeneratedAsset, GeneratedAsset.id == PublishingJob.generated_asset_id)
        .outerjoin(CreativeBrief, CreativeBrief.id == GeneratedAsset.creative_brief_id)
        .where(PublishingJob.business_id == business_id)
        .order_by(PostMetric.captured_at.desc())
        .limit(1000)
    )).all()

    # Keep the most recent metric snapshot per publishing job to avoid counting the same post repeatedly.
    latest = {}
    for metric, job, brief in rows:
        latest.setdefault(job.id, (metric, job, brief))

    platform_stats = defaultdict(list)
    content_stats = defaultdict(list)
    for metric, job, brief in latest.values():
        platform_stats[job.platform].append(metric.engagement_rate or 0.0)
        if brief:
            content_stats[brief.content_type].append(metric.engagement_rate or 0.0)

    platforms = [
        {"platform": p, "posts": len(v), "avg_engagement_rate": round(mean(v), 6)}
        for p, v in platform_stats.items()
    ]
    platforms.sort(key=lambda x: x["avg_engagement_rate"], reverse=True)

    formats = [
        {"content_type": t, "posts": len(v), "avg_engagement_rate": round(mean(v), 6)}
        for t, v in content_stats.items() if len(v) >= MIN_POSTS_FOR_WINNER
    ]
    formats.sort(key=lambda x: x["avg_engagement_rate"], reverse=True)

    return {
        "business": {"id": str(business.id), "name": business.name, "industry": business.industry, "city": business.city, "timezone": business.timezone},
        "brand": {
            "tone": brand.tone if brand else {},
            "audience": brand.audience if brand else {},
            "visual_style": brand.visual_style if brand else {},
            "brand_voice": brand.brand_voice if brand else {},
            "content_pillars": brand.content_pillars if brand else [],
            "cta_preferences": brand.cta_preferences if brand else [],
            "brand_rules": brand.brand_rules if brand else {},
        },
        "learning": {
            "total_posts_with_metrics": len(latest),
            "platforms": platforms,
            "validated_content_types": formats,
            "insights": [
                {"type": i.insight_type, "insight": i.insight, "evidence": i.evidence, "confidence": i.confidence}
                for i in insights
            ],
        },
        "guardrails": {
            "min_posts_for_content_winner": MIN_POSTS_FOR_WINNER,
            "do_not_overfit_single_post": True,
            "require_approval_before_publish": True,
        },
    }


def strategy_directives(context: dict) -> list[str]:
    directives = []
    learning = context.get("learning", {})
    platforms = learning.get("platforms", [])
    formats = learning.get("validated_content_types", [])
    if platforms:
        directives.append(f"Prioritize {platforms[0]['platform']} because it currently has the strongest measured average engagement.")
    if formats:
        directives.append(f"Increase experimentation around {formats[0]['content_type']} while keeping other pillars in the mix.")
    else:
        directives.append("No content format has enough evidence to declare a winner; keep the content mix diversified.")
    directives.append("Use performance data as a ranking signal, not as permission to publish automatically.")
    return directives
