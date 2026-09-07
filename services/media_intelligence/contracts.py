from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

class TimeRange(BaseModel):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)

class Scene(BaseModel):
    id: str
    time_range: TimeRange
    description: str = ""
    quality_score: float = Field(default=0, ge=0, le=1)
    subjects: list[str] = []

class TranscriptSegment(BaseModel):
    text: str
    time_range: TimeRange
    speaker: str | None = None
    confidence: float = Field(default=0, ge=0, le=1)

class DetectedEntity(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    time_ranges: list[TimeRange] = []
    attributes: dict = {}

class MediaQuality(BaseModel):
    width: int
    height: int
    duration_ms: int
    fps: float | None = None
    codec: str | None = None
    audio_present: bool = False
    blur_score: float | None = None
    exposure_score: float | None = None
    overall_score: float = Field(default=0, ge=0, le=1)

class ContentUnderstandingObject(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    asset_id: str
    summary: str = ""
    language: str | None = None
    media_quality: MediaQuality | None = None
    transcript: list[TranscriptSegment] = []
    scenes: list[Scene] = []
    entities: list[DetectedEntity] = []
    ocr_text: list[str] = []
    topics: list[str] = []
    offers: list[str] = []
    claims: list[str] = []
    suggested_hooks: list[str] = []
    safety_flags: list[str] = []
    source_hash: str | None = None
