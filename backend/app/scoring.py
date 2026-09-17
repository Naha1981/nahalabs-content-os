from math import isnan
from typing import Dict
from .models import BusinessProspect

WEIGHTS = {
    "social_gap": 0.25,
    "audience": 0.15,
    "historical_activity": 0.15,
    "business_health": 0.10,
    "content_dependency": 0.10,
    "monetization": 0.10,
    "competitive_gap": 0.05,
    "contactability": 0.05,
    "reputation": 0.05,
}


def social_gap_score(prospect: BusinessProspect) -> float:
    days = [c.last_meaningful_post_days for c in prospect.social_channels if c.last_meaningful_post_days is not None]
    if not days:
        return 0.0
    max_days = max(days)
    if max_days < 60:
        return 0.0
    if max_days < 90:
        return 45.0
    if max_days < 120:
        return 65.0
    if max_days < 180:
        return 78.0
    if max_days < 365:
        return 90.0
    return 100.0


def opportunity_score(prospect: BusinessProspect) -> float:
    values: Dict[str, float] = {
        "social_gap": social_gap_score(prospect),
        "audience": prospect.audience_score,
        "historical_activity": prospect.historical_activity_score,
        "business_health": prospect.health_score,
        "content_dependency": prospect.content_dependency_score,
        "monetization": prospect.monetization_score,
        "competitive_gap": prospect.competitive_gap_score,
        "contactability": prospect.contactability_score,
        "reputation": prospect.reputation_score,
    }
    total = sum(values[k] * WEIGHTS[k] for k in WEIGHTS)
    if isnan(total):
        raise ValueError("Score became NaN")
    return round(total, 2)


def grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    return "D"
