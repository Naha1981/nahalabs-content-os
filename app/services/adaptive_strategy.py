from __future__ import annotations
from collections import defaultdict
from statistics import mean
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Business, BrandProfile, ContentExperiment, CreativeBrief, GeneratedAsset, PostMetric, PublishingJob
from app.services.strategy_context import build_strategy_context, MIN_POSTS_FOR_WINNER


def _latest_metrics(rows):
    latest = {}
    for metric, job, brief in rows:
        latest.setdefault(job.id, (metric, job, brief))
    return list(latest.values())


async def build_adaptive_plan(db: AsyncSession, business_id, limit: int = 10) -> dict[str, Any]:
    context = await build_strategy_context(db, business_id)
    rows = (await db.execute(
        select(PostMetric, PublishingJob, CreativeBrief)
        .join(PublishingJob, PublishingJob.id == PostMetric.publishing_job_id)
        .join(GeneratedAsset, GeneratedAsset.id == PublishingJob.generated_asset_id)
        .outerjoin(CreativeBrief, CreativeBrief.id == GeneratedAsset.creative_brief_id)
        .where(PublishingJob.business_id == business_id)
        .order_by(PostMetric.captured_at.desc())
        .limit(2000)
    )).all()
    latest = _latest_metrics(rows)

    by_type = defaultdict(list)
    by_platform = defaultdict(list)
    for metric, job, brief in latest:
        by_platform[job.platform].append(metric.engagement_rate or 0.0)
        if brief:
            by_type[brief.content_type].append(metric.engagement_rate or 0.0)

    ranked_types = sorted(
        ((k, len(v), mean(v)) for k, v in by_type.items()),
        key=lambda x: x[2], reverse=True,
    )
    validated = [x for x in ranked_types if x[1] >= MIN_POSTS_FOR_WINNER]
    strongest_platform = max(by_platform.items(), key=lambda x: mean(x[1]))[0] if by_platform else None

    active_experiments = (await db.execute(
        select(ContentExperiment).where(
            ContentExperiment.business_id == business_id,
            ContentExperiment.status == "running",
        ).order_by(ContentExperiment.created_at.desc())
    )).scalars().all()

    recommendations: list[dict[str, Any]] = []
    if validated:
        winner = validated[0]
        recommendations.append({
            "action": "exploit",
            "content_type": winner[0],
            "reason": f"Validated by {winner[1]} measured posts with average engagement rate {winner[2]:.4f}.",
            "weight": 0.45,
        })
    else:
        recommendations.append({
            "action": "explore",
            "content_type": None,
            "reason": "No content type has enough evidence to declare a winner.",
            "weight": 0.35,
        })

    if strongest_platform:
        recommendations.append({
            "action": "prioritize_platform",
            "platform": strongest_platform,
            "reason": "Strongest measured platform in the current evidence window.",
            "weight": 0.25,
        })

    for exp in active_experiments:
        recommendations.append({
            "action": "continue_experiment",
            "experiment_id": str(exp.id),
            "variable": exp.variable,
            "reason": f"Active hypothesis: {exp.hypothesis}",
            "weight": 0.30,
        })

    # Fill remaining slots with diversified pillars from the brand rather than cloning the winner.
    pillars = context["brand"].get("content_pillars") or []
    for pillar in pillars[: max(0, limit - len(recommendations))]:
        recommendations.append({
            "action": "diversify",
            "content_pillar": pillar,
            "reason": "Preserve strategic variety while the system learns.",
            "weight": 0.10,
        })

    return {
        "business": context["business"],
        "evidence": context["learning"],
        "recommendations": recommendations[:limit],
        "experiments": [
            {"id": str(x.id), "name": x.name, "variable": x.variable, "status": x.status,
             "min_sample_size": x.min_sample_size, "winner": x.winner, "confidence": x.confidence}
            for x in active_experiments
        ],
        "guardrails": context["guardrails"],
    }


def choose_experiment_variant(experiment: ContentExperiment, sequence_number: int) -> str:
    """Deterministic assignment makes a batch reproducible and avoids hidden model decisions."""
    return "control" if sequence_number % 2 == 0 else "variant"
