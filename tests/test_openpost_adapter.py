from datetime import datetime, timezone

import httpx
import pytest

from app.adapters.openpost import OpenPostAdapter, OpenPostConfig


@pytest.mark.asyncio
async def test_create_publication_maps_nahalabs_asset_ids():
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"id": "pub_123", "revision": 1})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://openpost.test")
    adapter = OpenPostAdapter(
        OpenPostConfig(base_url="https://openpost.test", token="secret"),
        client=client,
    )

    result = await adapter.create_publication(
        workspace_id="ws_1",
        title="NahaLabs AutoPost",
        source_text="Build once. Adapt everywhere.",
        media_ids=["media_1", "media_2"],
        social_account_ids=["account_1"],
    )
    await client.aclose()

    assert result["id"] == "pub_123"
    assert requests[0].url.path == "/api/v1/publications"
    assert requests[0].headers["Authorization"] == "Bearer secret"
    payload = requests[0].read()
    assert b'"workspace_id":"ws_1"' in payload
    assert b'"media_id":"media_1"' in payload


@pytest.mark.asyncio
async def test_schedule_publication_uses_openpost_schedule_endpoint():
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"id": "pub_123", "status": "scheduled"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://openpost.test")
    adapter = OpenPostAdapter(
        OpenPostConfig(base_url="https://openpost.test", token="secret"),
        client=client,
    )

    result = await adapter.schedule_publication(
        "pub_123", datetime(2026, 9, 14, 8, 0, tzinfo=timezone.utc)
    )
    await client.aclose()

    assert result["status"] == "scheduled"
    assert requests[0].url.path == "/api/v1/publications/pub_123/schedule"
