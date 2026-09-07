from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class ConnectURLResponse(BaseModel):
    platform: str
    profile_id: str
    auth_url: str

class SocialAccountResponse(BaseModel):
    id: UUID
    platform: str
    username: str | None
    display_name: str | None
    status: str

class ApprovalCreate(BaseModel):
    scope: str = Field(pattern='^(once|batch|always)$')
    allowed_platforms: list[str] = Field(default_factory=list)
    allowed_content_types: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None

class ApprovalResponse(BaseModel):
    id: UUID
    scope: str
    allowed_platforms: list[str]
    allowed_content_types: list[str]
    expires_at: datetime | None
    revoked_at: datetime | None

class PublishCreate(BaseModel):
    generated_asset_id: UUID
    social_account_id: UUID
    scheduled_at: datetime | None = None
    caption: str | None = None
    custom_content: dict | None = None

class PublishingResponse(BaseModel):
    id: UUID
    status: str
    platform: str
    scheduled_at: datetime | None
    published_at: datetime | None
    external_post_id: str | None
    preflight_status: str = 'pending'
    preflight_result: dict = Field(default_factory=dict)
    approved_at: datetime | None = None


class PreflightResponse(BaseModel):
    valid: bool
    status: str
    message: str | None = None
    errors: list[dict] = Field(default_factory=list)
    warnings: list[dict] = Field(default_factory=list)
    checked_at: datetime

class ApprovalActionResponse(BaseModel):
    id: UUID
    status: str
    preflight_status: str
    approved_at: datetime | None
    published_at: datetime | None
    external_post_id: str | None
