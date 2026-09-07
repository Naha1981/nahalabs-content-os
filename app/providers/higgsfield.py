from __future__ import annotations
import httpx
from app.core.config import get_settings
from app.providers.contracts import GenerationRequest, GenerationResult

class HiggsfieldProvider:
    name = "higgsfield"
    def __init__(self) -> None:
        s = get_settings()
        self.base_url = s.higgsfield_api_base_url.rstrip("/")
        self.api_key = s.higgsfield_api_key
        self.submit_path = s.higgsfield_submit_path
        self.status_path = s.higgsfield_status_path

    def supports(self, operation: str) -> bool:
        return operation in {"polish_video", "video_transform"}

    async def submit(self, request: GenerationRequest) -> GenerationResult:
        if not self.api_key or not self.base_url:
            raise RuntimeError("Higgsfield provider is not configured")
        payload = {"operation": request.operation, "prompt": request.prompt,
                   "media_urls": request.media_urls, "model": request.model,
                   "duration_seconds": request.duration_seconds,
                   "aspect_ratio": request.aspect_ratio, "metadata": request.metadata}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{self.base_url}{self.submit_path}", json=payload,
                                  headers={"Authorization": f"Bearer {self.api_key}"})
            r.raise_for_status()
            data = r.json()
        return GenerationResult(provider=self.name, provider_job_id=str(data["id"]),
                                status=data.get("status", "queued"),
                                output_urls=data.get("output_urls", []),
                                estimated_cost=float(data.get("estimated_cost", 0)),
                                metadata=data)

    async def status(self, provider_job_id: str) -> GenerationResult:
        if not self.api_key or not self.base_url:
            raise RuntimeError("Higgsfield provider is not configured")
        path = self.status_path.format(job_id=provider_job_id)
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.base_url}{path}",
                                 headers={"Authorization": f"Bearer {self.api_key}"})
            r.raise_for_status()
            data = r.json()
        return GenerationResult(provider=self.name, provider_job_id=provider_job_id,
                                status=data.get("status", "unknown"),
                                output_urls=data.get("output_urls", []),
                                estimated_cost=float(data.get("estimated_cost", 0)),
                                metadata=data)
