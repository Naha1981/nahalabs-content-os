from __future__ import annotations

from typing import Any
from .models import BusinessProspect
from .scoring import opportunity_score, social_gap_score, grade


def social_gap_explanation(prospect: BusinessProspect) -> dict[str, Any]:
    channels = [c for c in prospect.social_channels if c.last_meaningful_post_days is not None]
    if not channels:
        return {
            "state": "NOT_VERIFIED",
            "headline": "Social activity is not yet verified.",
            "details": "No public post-date evidence was available, so the system will not claim a Social Gap.",
            "signals": [],
        }

    strongest = max(channels, key=lambda c: c.last_meaningful_post_days or 0)
    days = strongest.last_meaningful_post_days or 0
    historical = strongest.posts_last_365d or 0
    weekly = historical / 52

    if days < 60:
        headline = "No strong Social Gap detected."
        details = f"The latest meaningful activity on {strongest.platform} is about {days} days old."
    elif days < 90:
        headline = "Early Social Gap signal."
        details = f"The business has public historical activity, but its latest meaningful {strongest.platform} activity is about {days} days old."
    elif days < 180:
        headline = "Meaningful Social Gap detected."
        details = f"Historical activity exists, but meaningful {strongest.platform} activity has been absent for about {days} days."
    elif days < 365:
        headline = "Strong Social Gap detected."
        details = f"The account shows historical activity, while meaningful {strongest.platform} activity has been absent for about {days} days."
    else:
        headline = "Very strong Social Gap signal."
        details = f"The account has historical activity, but no meaningful {strongest.platform} activity has been observed for at least a year."

    return {
        "state": "OBSERVED",
        "headline": headline,
        "details": details,
        "signals": [
            {"label": "Channel", "value": strongest.platform},
            {"label": "Last meaningful post", "value": f"{days} days ago"},
            {"label": "Posts in 365 days", "value": historical},
            {"label": "Historical pace", "value": f"{weekly:.1f}/week"},
        ],
    }


def radar_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Turn an enriched prospect into a UI-safe, evidence-first radar record."""
    prospect = BusinessProspect.model_validate(raw)
    score = opportunity_score(prospect)
    gap = social_gap_score(prospect)
    evidence = [e.model_dump(mode="json") for e in prospect.evidence]
    # Keep only evidence with a clickable source. Pydantic already validates URLs.
    evidence = [e for e in evidence if e.get("source_url")]
    return {
        "name": prospect.name,
        "city": prospect.city,
        "category": prospect.category,
        "website": str(prospect.website),
        "google_url": str(prospect.google_url) if prospect.google_url else None,
        "phone": prospect.phone,
        "score": score,
        "grade": grade(score),
        "social_gap_score": gap,
        "social_gap": social_gap_explanation(prospect),
        "channels": [c.model_dump(mode="json") for c in prospect.social_channels],
        "evidence": evidence,
        "health_score": prospect.health_score,
        "audience_score": prospect.audience_score,
        "historical_activity_score": prospect.historical_activity_score,
        "content_dependency_score": prospect.content_dependency_score,
        "monetization_score": prospect.monetization_score,
        "competitive_gap_score": prospect.competitive_gap_score,
        "contactability_score": prospect.contactability_score,
        "reputation_score": prospect.reputation_score,
    }
