from __future__ import annotations
from typing import Any
import httpx
from app.core.config import get_settings
from app.providers.contracts import GenerationProvider, GenerationRequest, GenerationResult

class KIEProvider:
    name = "kie"
    def __init__(self) -> None:
        s = get_settings()
        self.base_url = s.kie_api_base_url.rstrip("/")
        self.api_key = s.kie_api_key
        self.submit_path = s.kie_submit_path
        self.status_path = s.kie_status_path
        self.model = s.kie_default_model

    def supports(self, operation: str) -> bool:
        return operation in {"generate_video", "generate_image", "generate_audio", "video_transform"}

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def submit(self, request: GenerationRequest) -> GenerationResult:
        if not self.api_key or not self.base_url:
            raise RuntimeError("KIE provider is not configured")
        payload: dict[str, Any] = {
            "model": request.model or self.model,
            "prompt": request.prompt,
            "aspect_ratio": request.aspect_ratio,
            "duration": request.duration_seconds,
            "media_urls": list(request.media_urls),
            "metadata": request.metadata,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{self.base_url}{self.submit_path}", headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
        job_id = data.get("id") or data.get("task_id") or data.get("job_id")
        if not job_id:
            raise RuntimeError("KIE response did not contain a provider job id")
        return GenerationResult(provider=self.name, provider_job_id=str(job_id), status=str(data.get("status", "queued")),
                                output_urls=tuple(data.get("output_urls") or data.get("urls") or ()),
                                model=str(data.get("model") or request.model or self.model), metadata=data)

    async def status(self, provider_job_id: str) -> GenerationResult:
        if not self.api_key or not self.base_url:
            raise RuntimeError("KIE provider is not configured")
        path = self.status_path.replace("{job_id}", provider_job_id)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(f"{self.base_url}{path}", headers=self._headers())
            response.raise_for_status()
            data = response.json()
        return GenerationResult(provider=self.name, provider_job_id=provider_job_id, status=str(data.get("status", "unknown")),
                                output_urls=tuple(data.get("output_urls") or data.get("urls") or ()),
                                model=data.get("model"), metadata=data)
