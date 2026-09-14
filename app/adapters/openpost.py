from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx


@dataclass(frozen=True)
class OpenPostConfig:
    base_url: str
    token: str
    timeout_seconds: float = 30.0


class OpenPostAdapter:
    """Thin NahaLabs boundary over OpenPost's HTTP API.

    NahaLabs keeps ownership of strategy, generation, quality and approval.
    OpenPost owns publication execution, destination renditions and scheduling.
    """

    def __init__(self, config: OpenPostConfig, client: httpx.AsyncClient | None = None):
        self.config = config
        self._client = client

    async def health(self) -> dict[str, Any]:
        return await self._request("GET", "/api/v1/health", authenticated=False)

    async def create_publication(
        self,
        *,
        workspace_id: str,
        title: str,
        source_text: str,
        content_profile: str = "short_text",
        media_ids: list[str] | None = None,
        social_account_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "workspace_id": workspace_id,
            "title": title[:80] or "Untitled",
            "content_profile": content_profile,
            "source_text": source_text,
            "social_account_ids": social_account_ids or [],
            "media": [{"media_id": media_id} for media_id in (media_ids or [])],
        }
        return await self._request("POST", "/api/v1/publications", json=payload)

    async def schedule_publication(
        self,
        publication_id: str,
        scheduled_at: datetime,
    ) -> dict[str, Any]:
        payload = {"scheduled_at": scheduled_at.isoformat()}
        return await self._request(
            "POST",
            f"/api/v1/publications/{publication_id}/schedule",
            json=payload,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if authenticated and self.config.token:
            headers["Authorization"] = f"Bearer {self.config.token}"

        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(
            base_url=self.config.base_url.rstrip("/"),
            timeout=self.config.timeout_seconds,
        )
        try:
            response = await client.request(method, path, json=json, headers=headers)
            response.raise_for_status()
            if not response.content:
                return {}
            return response.json()
        finally:
            if owns_client:
                await client.aclose()
