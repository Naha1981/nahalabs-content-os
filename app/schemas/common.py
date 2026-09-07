from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BusinessCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    industry: str | None = None
    description: str | None = None
    country: str | None = None
    city: str | None = None
    timezone: str = 'Africa/Johannesburg'
    website: HttpUrl | None = None
    whatsapp: str | None = None
    phone: str | None = None
    email: str | None = None


class BusinessOut(ORMModel):
    id: UUID
    organization_id: UUID
    name: str
    industry: str | None
    description: str | None
    country: str | None
    city: str | None
    timezone: str
    website: str | None
    whatsapp: str | None
    phone: str | None
    email: str | None
    status: str
    created_at: datetime


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=2, max_length=120, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


class OrganizationOut(ORMModel):
    id: UUID
    name: str
    slug: str
    status: str
    created_at: datetime


class UploadCreate(BaseModel):
    business_id: UUID
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str
    size_bytes: int = Field(gt=0)
    asset_type: str = 'video'


class UploadOut(BaseModel):
    asset_id: UUID
    storage_key: str
    upload_url: str
    expires_in: int


class UploadCompleteOut(BaseModel):
    source_media_id: UUID
    status: str


class ContentPackCreate(BaseModel):
    business_id: UUID
    name: str = Field(min_length=1, max_length=200)
    source_media_id: UUID
    objective: str | None = None
    platforms: list[str] = Field(default_factory=lambda: ['instagram', 'facebook', 'tiktok', 'youtube'])
    asset_target: int = Field(default=10, ge=1, le=50)


class ContentPackOut(ORMModel):
    id: UUID
    business_id: UUID
    name: str
    description: str | None
    source_media_id: UUID | None
    status: str
    asset_count: int
    strategy: dict
    created_at: datetime


class JobOut(ORMModel):
    id: UUID
    business_id: UUID
    content_pack_id: UUID | None
    job_type: str
    status: str
    attempts: int
    created_at: datetime
