from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from uuid import UUID
from app.providers.contracts import GenerationRequest, GenerationResult
from app.services.generation_router import GenerationRouter
from app.services.quality import QualityGate, QualityResult

@dataclass(frozen=True)
class FactoryResult:
    status: str
    provider: str | None = None
    provider_job_id: str | None = None
    quality: QualityResult | None = None
    metadata: dict[str, Any] | None = None

class ContentFactory:
    """Orchestrates production of one asset without owning provider-specific behavior."""
    def __init__(self, router: GenerationRouter | None = None, quality_gate: QualityGate | None = None) -> None:
        self.router = router or GenerationRouter()
        self.quality_gate = quality_gate or QualityGate()

    async def submit_asset(self, *, business_id: UUID, creative_brief_id: UUID, prompt: str,
                           operation: str = "generate_video", media_urls: tuple[str, ...] = (),
                           aspect_ratio: str = "9:16", duration_seconds: int | None = None,
                           metadata: dict[str, Any] | None = None) -> FactoryResult:
        request = GenerationRequest(operation=operation, prompt=prompt, media_urls=media_urls,
                                    aspect_ratio=aspect_ratio, duration_seconds=duration_seconds,
                                    metadata={"business_id": str(business_id), "creative_brief_id": str(creative_brief_id), **(metadata or {})})
        result: GenerationResult = await self.router.submit(request)
        return FactoryResult(status="provider_queued", provider=result.provider,
                             provider_job_id=result.provider_job_id, metadata={"provider_status": result.status})

    def quality_check(self, *, output_present: bool, metadata: dict[str, Any], aspect_ratio: str = "9:16") -> QualityResult:
        return self.quality_gate.evaluate(asset_type="video", metadata={"output_present": output_present, **metadata}, required_aspect_ratio=aspect_ratio)
