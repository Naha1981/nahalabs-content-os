from __future__ import annotations
from .contracts import ContentStrategy, CreativeBrief
from ..media_intelligence.contracts import ContentUnderstandingObject

DEFAULT_MIX = {
    "product_demo": 0.20,
    "educational": 0.20,
    "ugc": 0.20,
    "behind_the_scenes": 0.15,
    "offer": 0.15,
    "testimonial": 0.10,
}


def build_strategy(cuo: ContentUnderstandingObject, business: dict, count: int = 10) -> ContentStrategy:
    """Deterministic first-pass strategy. LLM generation plugs in later behind this contract."""
    business_name = business.get("name", "the business")
    audience = business.get("audience", "local customers")
    service = (cuo.entities[0].label if cuo.entities else "the product/service")
    hooks = cuo.suggested_hooks or [f"Here's what makes {service} different."]
    briefs: list[CreativeBrief] = []

    templates = [
        ("product_demo", f"Show {service} in action", "Demonstrate the result clearly."),
        ("educational", f"Teach one useful thing about {service}", "Give one practical takeaway."),
        ("ugc", f"Make {business_name} feel native to social media", "Use an authentic, conversational presentation."),
        ("behind_the_scenes", "Show what customers normally don't see", "Humanize the business."),
        ("offer", "Turn the footage into a clear offer", "Give customers a reason to act now."),
        ("testimonial", "Turn the real experience into social proof", "Use only claims supported by the source."),
    ]
    for i in range(count):
        ctype, objective, angle = templates[i % len(templates)]
        briefs.append(CreativeBrief(
            content_type=ctype,
            objective=objective,
            audience=audience,
            angle=angle,
            hook=hooks[i % len(hooks)],
            CTA=business.get("cta", "Contact us to learn more."),
            platforms=["instagram", "facebook", "tiktok", "youtube"],
            duration_seconds=15 if ctype != "carousel" else None,
            visual_direction={"preserve_subject_identity": True, "background_replacement_optional": True},
            copy_direction={"tone": business.get("tone", "authentic"), "avoid_unverified_claims": True},
            factual_claims=cuo.claims,
        ))
    return ContentStrategy(
        campaign_goal=f"Create a diverse social content pack for {business_name}",
        content_pillars=["education", "product", "trust", "personality", "conversion"],
        briefs=briefs,
    )
