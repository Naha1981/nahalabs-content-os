from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol
from uuid import UUID

AssetKind = Literal['video', 'image', 'carousel', 'audio']

@dataclass(frozen=True)
class GenerationRequest:
    business_id: UUID
    creative_brief_id: UUID
    asset_kind: AssetKind
    prompt: str
    duration_seconds: int | None = None
    aspect_ratio: str = '9:16'
    source_asset_keys: tuple[str, ...] = ()
    reference_image_keys: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class GenerationResult:
    provider_job_id: str
    provider: str
    model: str
    status: str
    output_urls: tuple[str, ...] = ()
    raw: dict[str, Any] = field(default_factory=dict)

class GenerationProvider(Protocol):
    name: str
    def submit(self, request: GenerationRequest) -> GenerationResult: ...
    def status(self, provider_job_id: str) -> GenerationResult: ...
    def cancel(self, provider_job_id: str) -> None: ...

@dataclass(frozen=True)
class RenderRequest:
    input_path: str
    output_path: str
    width: int
    height: int
    fps: int = 30
    start_seconds: float | None = None
    duration_seconds: float | None = None
    burn_captions: bool = False
    caption_file: str | None = None
    audio_path: str | None = None

class MediaRenderer(Protocol):
    def render(self, request: RenderRequest) -> str: ...
