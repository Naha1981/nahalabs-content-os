from __future__ import annotations
from typing import Any
import uuid
import httpx


class ZernioAdapter:
    """Infrastructure adapter isolating Zernio from NahaLabs domain logic.

    The SDK remains the default for normal operations. Critical post creation
    uses the REST endpoint directly so NahaLabs can explicitly supply Zernio's
    documented x-request-id idempotency header.
    """

    def __init__(self, api_key: str, base_url: str = "https://zernio.com/api/v1"):
        try:
            from zernio import Zernio
        except ImportError as exc:
            raise RuntimeError("zernio-sdk is required for publishing integration") from exc
        self.client = Zernio(api_key=api_key)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _value(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def _request(self, method: str, path: str, *, body: dict | None = None, headers: dict | None = None) -> dict:
        merged = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if headers:
            merged.update(headers)
        with httpx.Client(timeout=45.0) as client:
            response = client.request(method, f"{self.base_url}{path}", json=body, headers=merged)
        if response.status_code >= 400:
            detail = response.text[:4000]
            raise RuntimeError(f"Zernio HTTP {response.status_code}: {detail}")
        return response.json() if response.content else {}

    def create_profile(self, name: str) -> Any:
        profiles = self.client.profiles
        if hasattr(profiles, "create"):
            return profiles.create(name=name)
        return profiles.create_profile(name=name)

    def connect_url(self, platform: str, profile_id: str, redirect_url: str | None = None) -> str:
        connect = self.client.connect
        kwargs = {"platform": platform, "profile_id": profile_id}
        if redirect_url:
            kwargs["redirect_url"] = redirect_url
        if hasattr(connect, "get_connect_url"):
            result = connect.get_connect_url(**kwargs)
        else:
            result = connect.get_url(**kwargs)
        return str(self._value(result, "authUrl") or self._value(result, "auth_url") or result)

    def list_accounts(self, profile_id: str | None = None) -> Any:
        accounts = self.client.accounts
        if hasattr(accounts, "list"):
            return accounts.list(**({"profile_id": profile_id} if profile_id else {}))
        return accounts.list_accounts(**({"profile_id": profile_id} if profile_id else {}))

    def upload_media(self, local_path: str) -> str:
        result = self.client.media.upload(local_path)
        files = self._value(result, "files", [])
        if not files:
            raise RuntimeError("Zernio media upload returned no files")
        url = self._value(files[0], "url")
        if not url:
            raise RuntimeError("Zernio media upload returned no URL")
        return str(url)

    def create_post(self, *, content: str, account_id: str, platform: str,
                    media_url: str | None = None, media_type: str | None = None,
                    publish_now: bool = False, scheduled_for: str | None = None,
                    custom_content: str | None = None,
                    idempotency_key: str | None = None) -> Any:
        body: dict[str, Any] = {
            "content": content,
            "platforms": [{"platform": platform, "accountId": account_id}],
        }
        if custom_content:
            body["platforms"][0]["customContent"] = custom_content
        if media_url:
            body["mediaItems"] = [{"type": media_type or "video", "url": media_url}]
        if publish_now:
            body["publishNow"] = True
        elif scheduled_for:
            body["scheduledFor"] = scheduled_for
        key = idempotency_key or str(uuid.uuid4())
        return self._request("POST", "/posts", body=body, headers={"x-request-id": key})

    def validate_post(self, *, content: str | None, platform: str, account_id: str,
                      media_url: str | None = None, media_type: str | None = None,
                      custom_content: str | None = None) -> Any:
        body: dict[str, Any] = {
            "content": content or "",
            "platforms": [{"platform": platform, "accountId": account_id}],
        }
        if custom_content:
            body["platforms"][0]["customContent"] = custom_content
        if media_url:
            body["mediaItems"] = [{"type": media_type or "video", "url": media_url}]
        return self._request("POST", "/posts/validate", body=body)

    def get_post(self, post_id: str) -> Any:
        return self._request("GET", f"/posts/{post_id}")

    def delete_post(self, post_id: str) -> Any:
        return self._request("DELETE", f"/posts/{post_id}")

    def update_post(self, post_id: str, body: dict[str, Any]) -> Any:
        return self._request("PUT", f"/posts/{post_id}", body=body)

    def list_posts(self, **params: Any) -> Any:
        clean = {k: v for k, v in params.items() if v is not None}
        query = "&".join(f"{k}={httpx.QueryParams({k: v})[k]}" for k, v in clean.items())
        return self._request("GET", f"/posts?{query}" if query else "/posts")

    def get_analytics(self, **kwargs: Any) -> Any:
        analytics = self.client.analytics
        if hasattr(analytics, "get_analytics"):
            return analytics.get_analytics(**kwargs)
        if hasattr(analytics, "getAnalytics"):
            return analytics.getAnalytics(**kwargs)
        raise RuntimeError("Installed Zernio SDK does not expose analytics retrieval")
