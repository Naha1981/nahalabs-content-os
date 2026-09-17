from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Iterable, Optional


@dataclass(frozen=True)
class ActivityObservation:
    platform: str
    post_dates: list[datetime]


@dataclass(frozen=True)
class ActivitySummary:
    platform: str
    post_count_90d: int
    post_count_365d: int
    historical_posts_per_week: float
    last_post_days: Optional[int]
    inactivity_band: str
    historically_active: bool
    evidence_count: int


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _days_between(now: datetime, earlier: datetime) -> int:
    return max(0, (_as_utc(now) - _as_utc(earlier)).days)


def inactivity_band(days: Optional[int]) -> str:
    if days is None:
        return "NOT_VERIFIED"
    if days < 60:
        return "UNDER_60_DAYS"
    if days < 90:
        return "60_89_DAYS"
    if days < 120:
        return "90_119_DAYS"
    if days < 180:
        return "120_179_DAYS"
    if days < 365:
        return "180_364_DAYS"
    return "365_PLUS_DAYS"


def analyse_channel(
    observation: ActivityObservation,
    now: Optional[datetime] = None,
    historical_window_days: int = 365,
) -> ActivitySummary:
    now = _as_utc(now or datetime.now(timezone.utc))
    dates = sorted(
        {_as_utc(d) for d in observation.post_dates if _as_utc(d) <= now},
        reverse=True,
    )
    recent_365 = [d for d in dates if _days_between(now, d) <= historical_window_days]
    recent_90 = [d for d in dates if _days_between(now, d) <= 90]
    last_days = _days_between(now, dates[0]) if dates else None
    weekly = len(recent_365) / (historical_window_days / 7)

    return ActivitySummary(
        platform=observation.platform,
        post_count_90d=len(recent_90),
        post_count_365d=len(recent_365),
        historical_posts_per_week=round(weekly, 2),
        last_post_days=last_days,
        inactivity_band=inactivity_band(last_days),
        historically_active=weekly >= 2.0,
        evidence_count=len(dates),
    )


def historical_activity_score(summaries: Iterable[ActivitySummary]) -> float:
    summaries = list(summaries)
    if not summaries:
        return 0.0

    active = [s for s in summaries if s.historically_active]
    if not active:
        return 25.0

    max_weekly = max(s.historical_posts_per_week for s in active)
    if max_weekly >= 5:
        return 100.0
    if max_weekly >= 2:
        return 90.0
    if max_weekly >= 1:
        return 70.0
    return 50.0


def social_gap_from_activity(summaries: Iterable[ActivitySummary]) -> float:
    summaries = list(summaries)
    days = [s.last_post_days for s in summaries if s.last_post_days is not None]
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
