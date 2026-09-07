from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class CreativeBriefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    content_pack_id: UUID
    content_type: str
    objective: str
    angle: str
    hook: str
    audience: str | None
    cta: str | None
    platforms: list[str]
    duration_seconds: int | None
    visual_direction: dict
    copy_direction: dict
    status: str
    created_at: datetime

class GenerateAssetRequest(BaseModel):
    creative_brief_id: UUID
    asset_type: str = Field(default='video', pattern='^(video|image|carousel)$')
    provider: str = 'kie'
    polish_requested: bool = False
    polish_prompt: str | None = None
    aspect_ratio: str = Field(default='9:16', pattern='^\\d+:\\d+$')

class GeneratedAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    content_pack_id: UUID
    creative_brief_id: UUID
    media_asset_id: UUID | None
    asset_type: str
    status: str
    version: int
    generation_provider: str | None
    generation_model: str | None
    provider_job_id: str | None
    quality_score: float | None
    brand_score: float | None
    platform_score: float | None
    created_at: datetime
