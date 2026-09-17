from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .activity import ActivityObservation, analyse_channel

SUPPORTED = {"instagram", "facebook", "tiktok", "youtube", "linkedin", "x"}


def platform_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if "instagram.com" in host:
        return "instagram"
    if "facebook.com" in host or "fb.com" in host:
        return "facebook"
    if "tiktok.com" in host:
        return "tiktok"
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "linkedin.com" in host:
        return "linkedin"
    if "x.com" in host or "twitter.com" in host:
        return "x"
    return "unknown"


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    candidates = [value.replace("Z", "+00:00"), value]
    for candidate in candidates:
        try:
            dt = datetime.fromisoformat(candidate)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def _walk_json(value: Any, dates: list[datetime], followers: list[int]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_l = str(key).lower()
            if key_l in {"datepublished", "datecreated", "upload_date", "date"} and isinstance(child, str):
                parsed = _parse_date(child)
                if parsed:
                    dates.append(parsed)
            if key_l in {"interactioncount", "followers", "followcount", "subscriber_count"}:
                if isinstance(child, (int, float)):
                    followers.append(int(child))
                elif isinstance(child, str):
                    m = re.search(r"[0-9][0-9,]*", child)
                    if m:
                        followers.append(int(m.group(0).replace(",", "")))
            _walk_json(child, dates, followers)
    elif isinstance(value, list):
        for child in value:
            _walk_json(child, dates, followers)


def extract_social_evidence(html: str, source_url: str, now: datetime | None = None) -> dict:
    """Extract only publicly visible/embedded evidence; never infer missing metrics."""
    soup = BeautifulSoup(html, "html.parser")
    platform = platform_from_url(source_url)
    if platform not in SUPPORTED:
        return {"platform": platform, "url": source_url, "post_dates": [], "followers": None, "evidence": []}

    dates: list[datetime] = []
    followers: list[int] = []
    evidence: list[dict[str, str]] = []

    for tag in soup.find_all("time"):
        dt = _parse_date(tag.get("datetime"))
        if dt:
            dates.append(dt)

    for meta in soup.find_all("meta"):
        key = (meta.get("property") or meta.get("name") or "").lower()
        content = meta.get("content")
        if key in {"article:published_time", "og:published_time", "datepublished"}:
            dt = _parse_date(content)
            if dt:
                dates.append(dt)
        if content and ("follower" in key or "subscriber" in key):
            m = re.search(r"[0-9][0-9,]*", content)
            if m:
                followers.append(int(m.group(0).replace(",", "")))

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            payload = json.loads(script.string or script.get_text())
            _walk_json(payload, dates, followers)
        except (json.JSONDecodeError, TypeError):
            continue

    unique_dates = sorted({d.isoformat() for d in dates}, reverse=True)
    follower_count = max(followers) if followers else None
    observed_at = (now or datetime.now(timezone.utc)).isoformat()

    if unique_dates:
        evidence.append({
            "claim": "public_post_date",
            "value": unique_dates[0],
            "source_url": source_url,
            "state": "OBSERVED",
            "observed_at": observed_at,
        })
    if follower_count is not None:
        evidence.append({
            "claim": "public_audience_count",
            "value": str(follower_count),
            "source_url": source_url,
            "state": "OBSERVED",
            "observed_at": observed_at,
        })

    activity = analyse_channel(
        ActivityObservation(platform, [datetime.fromisoformat(d) for d in unique_dates]),
        now=now,
    )

    return {
        "platform": platform,
        "url": source_url,
        "post_dates": unique_dates,
        "followers": follower_count,
        "evidence": evidence,
        "activity": activity.__dict__,
    }
