from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

BASE_URL = "https://api.kie.ai"
DEFAULT_MODEL = "veo-3-1"


class KIEUnavailable(RuntimeError):
    pass


class KIETaskError(RuntimeError):
    pass


def _request(method: str, path: str, api_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise KIETaskError(f"KIE HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise KIEUnavailable(f"KIE network error: {exc.reason}") from exc


def _api_key() -> str:
    key = os.getenv("KIE_API_KEY", "").strip()
    if not key:
        raise KIEUnavailable("KIE_API_KEY is not configured")
    return key


def build_prompt(job: dict[str, Any]) -> str:
    shots = " | ".join(job.get("shot_list") or [])
    return (
        "Create a short vertical social-media video for a real local business. "
        "Use natural South African commercial realism, authentic human activity, "
        "credible local-business atmosphere, no invented logos, no fabricated claims. "
        f"Business content title: {job.get('title', '')}. "
        f"Hook: {job.get('hook', '')}. "
        f"Voiceover/script intent: {job.get('voiceover', '')}. "
        f"CTA: {job.get('cta', '')}. "
        f"Shot guidance: {shots}. "
        "Keep the visual story simple and suitable for a social reel."
    )


def submit_kie_video(job: dict[str, Any], *, model: str = DEFAULT_MODEL, callback_url: str = "") -> dict[str, Any]:
    key = _api_key()
    # Veo 3.1 supports explicit 9:16 output; use an 8-second clip as the provider
    # unit. Longer social assets can later be assembled from multiple provider jobs.
    aspect = "9:16" if job.get("aspect_ratio") == "9:16" else "16:9"
    payload = {
        "model": model,
        "input": {
            "prompt": build_prompt(job),
            "aspect_ratio": aspect,
            "resolution": "720p",
            "duration": 8,
            "enable_fallback": False,
            "enable_translation": True,
        },
    }
    if callback_url.strip():
        payload["callBackUrl"] = callback_url.strip()
    response = _request("POST", "/api/v1/jobs/createTask", key, payload)
    data = response.get("data") or {}
    task_id = data.get("taskId")
    if response.get("code") not in (None, 200) or not task_id:
        raise KIETaskError(response.get("msg") or "KIE did not return a taskId")
    return {"provider": "KIE", "model": model, "task_id": task_id, "state": "waiting", "response": response}


def get_kie_task(task_id: str) -> dict[str, Any]:
    key = _api_key()
    query = urlencode({"taskId": task_id})
    response = _request("GET", f"/api/v1/jobs/recordInfo?{query}", key)
    data = response.get("data") or {}
    state = data.get("state", "unknown")
    result_urls: list[str] = []
    raw_result = data.get("resultJson")
    if raw_result:
        try:
            parsed = json.loads(raw_result) if isinstance(raw_result, str) else raw_result
            result_urls = parsed.get("resultUrls") or []
        except (TypeError, json.JSONDecodeError):
            pass
    return {
        "provider": "KIE",
        "task_id": task_id,
        "state": state,
        "result_urls": result_urls,
        "progress": data.get("progress"),
        "credits_consumed": data.get("creditsConsumed"),
        "fail_code": data.get("failCode", ""),
        "fail_message": data.get("failMsg", ""),
        "response": response,
    }
