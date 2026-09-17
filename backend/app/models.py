from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional


class EvidenceState(str, Enum):
    OBSERVED = "OBSERVED"
    VERIFIED = "VERIFIED"
    INFERRED = "INFERRED"
    HYPOTHESIS = "HYPOTHESIS"


class Evidence(BaseModel):
    claim: str
    value: str
    source_url: HttpUrl
    state: EvidenceState
    observed_at: Optional[str] = None


class SocialChannel(BaseModel):
    platform: str
    url: HttpUrl
    followers: Optional[int] = Field(default=None, ge=0)
    posts_last_90d: Optional[int] = Field(default=None, ge=0)
    posts_last_365d: Optional[int] = Field(default=None, ge=0)
    last_meaningful_post_days: Optional[int] = Field(default=None, ge=0)


class Competitor(BaseModel):
    name: str
    url: HttpUrl
    posts_last_30d: Optional[int] = Field(default=None, ge=0)


class BusinessProspect(BaseModel):
    name: str
    city: str
    website: HttpUrl
    google_url: Optional[HttpUrl] = None
    phone: Optional[str] = None
    category: str
    health_score: float = Field(ge=0, le=100)
    content_dependency_score: float = Field(ge=0, le=100)
    monetization_score: float = Field(ge=0, le=100)
    reputation_score: float = Field(ge=0, le=100)
    historical_activity_score: float = Field(ge=0, le=100)
    audience_score: float = Field(ge=0, le=100)
    competitive_gap_score: float = Field(ge=0, le=100)
    contactability_score: float = Field(ge=0, le=100)
    social_channels: List[SocialChannel] = []
    competitors: List[Competitor] = []
    evidence: List[Evidence] = []
