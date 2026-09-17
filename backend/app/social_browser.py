from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from .social_evidence import extract_social_evidence, platform_from_url
from .playwright_windows import (
    cleanup_sync_playwright_event_loop,
    prepare_sync_playwright_event_loop,
)

DEFAULT_TIMEOUT_MS = 25_000
DEFAULT_SCROLLS = 2


def _normalise_public_url(url: str) -> str:
    value = (url or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("A public http(s) URL is required")
    return value


def collect_social_url(
    url: str,
    *,
    headless: bool = True,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    scrolls: int = DEFAULT_SCROLLS,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Render a public social URL and extract only evidence exposed by the page.

    This collector does not log in, submit forms, send messages, or bypass access
    controls. Dynamic content is collected from the public rendered page only.
    """
    target = _normalise_public_url(url)
    observed_at = (now or datetime.now(timezone.utc)).isoformat()
    platform = platform_from_url(target)

    if platform == "unknown":
        return {
            "status": "NOT_VERIFIED",
            "platform": platform,
            "url": target,
            "final_url": target,
            "title": None,
            "evidence": [],
            "activity": {"inactivity_band": "NOT_VERIFIED"},
            "observed_at": observed_at,
            "error": "Unsupported social platform URL",
        }

    browser = None
    loop = prepare_sync_playwright_event_loop()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                locale="en-ZA",
                viewport={"width": 1440, "height": 1000},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0 Safari/537.36 NahaLabs-Reactivate/0.7"
                ),
            )
            page = context.new_page()
            page.goto(target, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(1800)

            for _ in range(max(0, min(scrolls, 5))):
                page.mouse.wheel(0, 1400)
                page.wait_for_timeout(700)

            html = page.content()
            final_url = page.url
            title = page.title()
            evidence = extract_social_evidence(html, final_url, now=now)

            return {
                "status": "OBSERVED",
                "platform": platform_from_url(final_url) or platform,
                "url": target,
                "final_url": final_url,
                "title": title,
                "content_length": len(html),
                "post_dates": evidence.get("post_dates", []),
                "followers": evidence.get("followers"),
                "evidence": evidence.get("evidence", []),
                "activity": evidence.get("activity", {"inactivity_band": "NOT_VERIFIED"}),
                "observed_at": observed_at,
            }
    except Exception as exc:
        return {
            "status": "NOT_VERIFIED",
            "platform": platform,
            "url": target,
            "final_url": target,
            "title": None,
            "evidence": [],
            "activity": {"inactivity_band": "NOT_VERIFIED"},
            "observed_at": observed_at,
            "error": str(exc),
        }
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        cleanup_sync_playwright_event_loop(loop)


def collect_social_urls(urls: dict[str, str], *, headless: bool = True, now: datetime | None = None) -> dict[str, Any]:
    """Collect a set of already-discovered official social URLs."""
    results: dict[str, Any] = {}
    for platform, url in urls.items():
        if not url:
            continue
        results[platform] = collect_social_url(url, headless=headless, now=now)
    return results
