from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

SOCIAL_HOSTS = {
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "tiktok": "tiktok.com",
    "youtube": "youtube.com",
    "linkedin": "linkedin.com",
    "x": "x.com",
}


@dataclass
class DiscoveredBusiness:
    name: str
    address: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None
    google_url: Optional[str] = None
    phone: Optional[str] = None
    social_urls: dict[str, str] | None = None
    source_url: Optional[str] = None


def _clean_url(url: str) -> str:
    return url.split("#", 1)[0].rstrip("/")


def extract_social_links(html: str) -> dict[str, str]:
    """Extract public social profile links from a page without guessing profiles."""
    soup = BeautifulSoup(html, "html.parser")
    found: dict[str, str] = {}
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        lower = href.lower()
        for platform, host in SOCIAL_HOSTS.items():
            if host in lower and platform not in found:
                found[platform] = _clean_url(href)
    return found


def extract_contact_details(html: str) -> tuple[Optional[str], Optional[str]]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    phone = None
    match = re.search(r"(?:\+27|0)[\s.-]?\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}", text)
    if match:
        phone = match.group(0)
    website = None
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        if href.startswith(("http://", "https://")) and not any(host in href.lower() for host in SOCIAL_HOSTS.values()):
            website = _clean_url(href)
            break
    return phone, website


def maps_search_url(query: str, location: str) -> str:
    """Return a navigational Maps URL; browser automation can resolve result cards later."""
    return f"https://www.google.com/maps/search/{quote_plus(f'{query} {location}') }"
