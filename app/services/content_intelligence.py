from __future__ import annotations
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import BrandProfile, Business, ContentPack, CreativeBrief, SourceMedia
from app.services.strategy_context import build_strategy_context
from app.services.adaptive_strategy import choose_experiment_variant
from app.models import ContentExperiment

BASE_PILLARS = ["product_demo", "education", "behind_the_scenes", "offer", "social_proof", "story"]
HOOKS = {
    "product_demo": "Show the product/service in action and make the value obvious in the first 2 seconds.",
    "education": "Teach one useful thing the target customer can apply immediately.",
    "behind_the_scenes": "Reveal the real people and process behind the business.",
    "offer": "Present a clear, truthful reason to take action now without inventing urgency.",
    "social_proof": "Demonstrate a real customer outcome, review, process, or proof point; never fabricate a testimonial.",
    "story": "Tell a short founder, customer, product, or local-business story with a clear emotional turn.",
}


def _ranked_pillars(context: dict[str, Any], count: int) -> list[str]:
    brand = context.get("brand", {})
    pillars = [p for p in (brand.get("content_pillars") or []) if p]
    validated = context.get("learning", {}).get("validated_content_types", [])
    winners = [x["content_type"] for x in validated]
    ordered = []
    # Exploit evidence, but reserve slots for exploration/diversification.
    for p in winners:
        if p not in ordered:
            ordered.append(p)
    for p in pillars:
        if p not in ordered:
            ordered.append(p)
    for p in BASE_PILLARS:
        if p not in ordered:
            ordered.append(p)
    return [ordered[i % len(ordered)] for i in range(count)] if ordered else BASE_PILLARS[:count]


def _platforms(context: dict[str, Any]) -> list[str]:
    platforms = context.get("learning", {}).get("platforms", [])
    if platforms:
        return [platforms[0]["platform"]]
    return ["instagram", "facebook", "tiktok"]


def _best_experiment(experiments: list[ContentExperiment]) -> ContentExperiment | None:
    running = [e for e in experiments if e.status == "running"]
    return running[0] if running else None


async def generate_content_intelligence_plan(
    db: AsyncSession,
    business_id: uuid.UUID,
    asset_count: int = 10,
    source_media_id: uuid.UUID | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    context = await build_strategy_context(db, business_id)
    business = await db.get(Business, business_id)
    if not business:
        raise ValueError("Business not found")
    if source_media_id is not None:
        source = await db.get(SourceMedia, source_media_id)
        if not source or source.business_id != business_id:
            raise ValueError("Source media not found for business")

    experiments = (await db.execute(
        select(ContentExperiment)
        .where(ContentExperiment.business_id == business_id, ContentExperiment.status == "running")
        .order_by(ContentExperiment.created_at.desc())
    )).scalars().all()
    experiment = _best_experiment(experiments)
    platforms = _platforms(context)
    pillars = _ranked_pillars(context, asset_count)
    validated = context.get("learning", {}).get("validated_content_types", [])
    winner = validated[0]["content_type"] if validated else None

    pack = ContentPack(
        business_id=business_id,
        source_media_id=source_media_id,
        name=f"Adaptive Content Pack — {business.name}",
        description="Strategy-generated content plan based on Brand DNA and measured performance.",
        status="planned",
        asset_count=asset_count,
        strategy={
            "engine": "content-intelligence-v1.3",
            "evidence_posts": context["learning"]["total_posts_with_metrics"],
            "validated_winner": winner,
            "platform_priority": platforms[0] if platforms else None,
            "experiment_id": str(experiment.id) if experiment else None,
        },
    )
    if persist:
        db.add(pack)
        await db.flush()
    else:
        pack.id = uuid.uuid4()

    briefs = []
    for i, pillar in enumerate(pillars):
        variant = None
        experiment_config = None
        if experiment:
            variant = choose_experiment_variant(experiment, i)
            experiment_config = experiment.control if variant == "control" else experiment.variant
        angle = f"{pillar.replace('_', ' ').title()} angle #{i + 1}"
        if variant:
            angle += f" — {variant}"
        brief = CreativeBrief(
            content_pack_id=pack.id,
            content_type=pillar,
            objective="Drive useful attention and measurable action while preserving strategic variety.",
            angle=angle,
            hook=HOOKS.get(pillar, "Create a clear, useful story around the business."),
            audience=str(context["brand"].get("audience") or "local customers"),
            cta=(context["brand"].get("cta_preferences") or ["Visit us", "DM us", "Book now"])[i % len(context["brand"].get("cta_preferences") or ["Visit us", "DM us", "Book now"])],
            platforms=platforms,
            duration_seconds=30,
            visual_direction={"source_first": True, "higgsfield_polish": "conditional"},
            copy_direction={"tone": context["brand"].get("tone", {}), "factual_only": True},
            status="planned",
            strategy_metadata={
                "engine": "content-intelligence-v1.3",
                "rank": i + 1,
                "pillar": pillar,
                "evidence": {"validated_winner": winner, "sample_size": context["learning"]["total_posts_with_metrics"]},
                "experiment": {"id": str(experiment.id), "variant": variant, "configuration": experiment_config} if experiment else None,
            },
        )
        if persist:
            db.add(brief)
        else:
            brief.id = uuid.uuid4()
        briefs.append(brief)

    if persist:
        await db.commit()
        for brief in briefs:
            await db.refresh(brief)
        await db.refresh(pack)
    return {
        "content_pack_id": str(pack.id),
        "business_id": str(business_id),
        "engine": "content-intelligence-v1.3",
        "asset_count": asset_count,
        "evidence_posts": context["learning"]["total_posts_with_metrics"],
        "validated_winner": winner,
        "platform_priority": platforms[0] if platforms else None,
        "experiment_id": str(experiment.id) if experiment else None,
        "briefs": [
            {
                "id": str(b.id),
                "rank": i + 1,
                "content_type": b.content_type,
                "angle": b.angle,
                "hook": b.hook,
                "cta": b.cta,
                "platforms": b.platforms,
                "strategy_metadata": b.strategy_metadata,
            }
            for i, b in enumerate(briefs)
        ],
    }
