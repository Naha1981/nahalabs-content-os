from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from .discovery import extract_contact_details, extract_social_links

DEFAULT_TIMEOUT = 12.0


def _normalise_url(url: str | None) -> str | None:
    if not url:
        return None
    value = url.strip()
    if not value:
        return None
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value


def inspect_website(url: str, client: httpx.Client | None = None) -> dict[str, Any]:
    """Inspect a public business homepage and return evidence only from observed HTML."""
    target = _normalise_url(url)
    if not target:
        return {"status": "NOT_VERIFIED", "error": "Invalid website URL", "social_urls": {}}

    own_client = client is None
    client = client or httpx.Client(
        follow_redirects=True,
        timeout=DEFAULT_TIMEOUT,
        headers={"User-Agent": "NahaLabs-Reactivate/0.3 public research worker"},
    )
    observed_at = datetime.now(timezone.utc).isoformat()
    try:
        response = client.get(target)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return {
                "status": "OBSERVED",
                "url": str(response.url),
                "status_code": response.status_code,
                "content_type": content_type,
                "social_urls": {},
                "phone": None,
                "evidence": [],
                "observed_at": observed_at,
            }

        phone, _ = extract_contact_details(response.text)
        social_urls = extract_social_links(response.text)
        evidence = [
            {
                "claim": "website",
                "value": str(response.url),
                "source_url": str(response.url),
                "state": "OBSERVED",
                "observed_at": observed_at,
            }
        ]
        if phone:
            evidence.append({
                "claim": "public_phone",
                "value": phone,
                "source_url": str(response.url),
                "state": "OBSERVED",
                "observed_at": observed_at,
            })
        for platform, social_url in social_urls.items():
            evidence.append({
                "claim": f"official_{platform}_link",
                "value": social_url,
                "source_url": str(response.url),
                "state": "OBSERVED",
                "observed_at": observed_at,
            })

        return {
            "status": "OBSERVED",
            "url": str(response.url),
            "status_code": response.status_code,
            "content_type": content_type,
            "social_urls": social_urls,
            "phone": phone,
            "evidence": evidence,
            "observed_at": observed_at,
        }
    except (httpx.HTTPError, httpx.TimeoutException) as exc:
        return {
            "status": "NOT_VERIFIED",
            "url": target,
            "error": str(exc),
            "social_urls": {},
            "phone": None,
            "evidence": [],
            "observed_at": observed_at,
        }
    finally:
        if own_client:
            client.close()


def enrich_business(business: dict[str, Any], client: httpx.Client | None = None) -> dict[str, Any]:
    """Enrich one discovery record using its own public website, when available."""
    enriched = dict(business)
    website = business.get("website")
    if not website:
        enriched.update({
            "enrichment_status": "NO_WEBSITE_FOUND",
            "social_urls": business.get("social_urls") or {},
            "evidence": [],
        })
        return enriched

    inspection = inspect_website(website, client=client)
    enriched["website"] = inspection.get("url", website)
    enriched["phone"] = inspection.get("phone") or business.get("phone")
    enriched["social_urls"] = inspection.get("social_urls") or business.get("social_urls") or {}
    enriched["enrichment_status"] = inspection["status"]
    enriched["evidence"] = inspection.get("evidence", [])
    enriched["observed_at"] = inspection.get("observed_at")
    return enriched
