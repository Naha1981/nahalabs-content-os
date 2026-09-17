from __future__ import annotations

from datetime import datetime
from typing import Any

from .activity import ActivityObservation, analyse_channel, historical_activity_score, social_gap_from_activity
from .social_browser import collect_social_urls


def enrich_social_profiles(
    social_urls: dict[str, str],
    *,
    headless: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Collect public social evidence and normalize it into scoring-ready channel data."""
    raw = collect_social_urls(social_urls, headless=headless, now=now)
    channels: list[dict[str, Any]] = []
    summaries = []

    for platform, result in raw.items():
        dates = [datetime.fromisoformat(value) for value in result.get("post_dates", [])]
        summary = analyse_channel(ActivityObservation(platform, dates), now=now)
        summaries.append(summary)
        channels.append({
            "platform": platform,
            "url": result.get("final_url") or result.get("url"),
            "followers": result.get("followers"),
            "posts_last_90d": summary.post_count_90d,
            "posts_last_365d": summary.post_count_365d,
            "last_meaningful_post_days": summary.last_post_days,
            "historical_posts_per_week": summary.historical_posts_per_week,
            "inactivity_band": summary.inactivity_band,
            "historically_active": summary.historically_active,
            "evidence_count": summary.evidence_count,
            "status": result.get("status"),
            "evidence": result.get("evidence", []),
            "error": result.get("error"),
        })

    return {
        "channels": channels,
        "historical_activity_score": historical_activity_score(summaries),
        "social_gap_score": social_gap_from_activity(summaries),
        "evidence_state": "OBSERVED" if any(c["evidence_count"] for c in channels) else "NOT_VERIFIED",
    }
