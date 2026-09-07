from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

ContentType = Literal[
    "reel", "ugc", "carousel", "story", "image_post", "testimonial",
    "educational", "offer", "behind_the_scenes", "product_demo"
]

class CreativeBrief(BaseModel):
    content_type: ContentType
    objective: str
    audience: str
    angle: str
    hook: str
    CTA: str
    platforms: list[str]
    duration_seconds: int | None = Field(default=None, ge=3, le=180)
    visual_direction: dict = {}
    copy_direction: dict = {}
    source_ranges_ms: list[tuple[int, int]] = []
    factual_claims: list[str] = []

class ContentStrategy(BaseModel):
    strategy_version: str = "1.0"
    campaign_goal: str
    content_pillars: list[str]
    briefs: list[CreativeBrief]
