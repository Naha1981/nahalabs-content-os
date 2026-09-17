from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from playwright.sync_api import sync_playwright

from .discovery import DiscoveredBusiness
from .playwright_windows import (
    cleanup_sync_playwright_event_loop,
    prepare_sync_playwright_event_loop,
)


def _text(locator) -> Optional[str]:
    try:
        value = locator.inner_text(timeout=1500).strip()
        return value or None
    except Exception:
        return None


def discover_google_maps(query: str, location: str, limit: int = 10, headless: bool = True) -> list[dict]:
    """Discover public Google Maps result cards.

    This worker only records data visible in the public Maps result UI. It does not
    attempt to infer owners, social handles, or contact details that Maps does not show.
    """
    limit = max(1, min(limit, 50))
    search_url = f"https://www.google.com/maps/search/?api=1&query={query.replace(' ', '+')}+{location.replace(' ', '+')}"
    results: list[DiscoveredBusiness] = []

    loop = prepare_sync_playwright_event_loop()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page(viewport={"width": 1440, "height": 1000}, locale="en-ZA")
            try:
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2500)

                cards = page.locator('div[role="feed"] div[role="article"]')
                seen: set[str] = set()
                stagnant = 0
                while len(results) < limit and stagnant < 3:
                    count = cards.count()
                    before = len(results)
                    for i in range(count):
                        card = cards.nth(i)
                        name = _text(card.locator('div.fontHeadlineSmall').first)
                        if not name or name in seen:
                            continue
                        seen.add(name)
                        href = None
                        try:
                            href = card.locator('a[href*="/maps/place/"]').first.get_attribute("href")
                        except Exception:
                            pass
                        results.append(DiscoveredBusiness(name=name, google_url=href, source_url=search_url))
                        if len(results) >= limit:
                            break
                    stagnant = stagnant + 1 if len(results) == before else 0
                    if len(results) < limit:
                        try:
                            feed = page.locator('div[role="feed"]')
                            feed.evaluate("el => el.scrollTop = el.scrollHeight")
                        except Exception:
                            break
                        page.wait_for_timeout(1200)
            finally:
                browser.close()
    finally:
        cleanup_sync_playwright_event_loop(loop)

    return [asdict(item) for item in results]
