from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol

@dataclass(frozen=True)
class GenerationRequest:
    operation: str
    prompt: str
    media_urls: tuple[str, ...] = ()
    model: str | None = None
    duration_seconds: int | None = None
    aspect_ratio: str = "9:16"
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class GenerationResult:
    provider: str
    provider_job_id: str
    status: str
    output_urls: tuple[str, ...] = ()
    model: str | None = None
    estimated_cost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

class GenerationProvider(Protocol):
    name: str
    def supports(self, operation: str) -> bool: ...
    async def submit(self, request: GenerationRequest) -> GenerationResult: ...
    async def status(self, provider_job_id: str) -> GenerationResult: ...
