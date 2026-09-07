from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
class QualityCheckOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: UUID
    generated_asset_id: UUID
    status: str
    overall_score: float
    technical_score: float
    visual_score: float
    brand_score: float
    platform_score: float
    safety_score: float
    issues: list
    warnings: list
    evidence: dict
    checked_at: datetime
