from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.zernio import ZernioAdapter
from app.models import ApprovalGrant, Business, GeneratedAsset, PublishingJob, SocialAccount, ZernioProfile

class PublishingService:
    def __init__(self, db: AsyncSession, adapter: ZernioAdapter):
        self.db, self.adapter = db, adapter

    async def ensure_profile(self, business: Business) -> ZernioProfile:
        result = await self.db.execute(select(ZernioProfile).where(ZernioProfile.business_id == business.id))
        profile = result.scalar_one_or_none()
        if profile:
            return profile
        external = self.adapter.create_profile(name=business.name)
        external_id = str(external.get('id') if isinstance(external, dict) else getattr(external, 'id', external))
        profile = ZernioProfile(business_id=business.id, external_profile_id=external_id)
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def active_grant(self, business_id: uuid.UUID, platform: str, content_type: str) -> ApprovalGrant | None:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(select(ApprovalGrant).where(
            ApprovalGrant.business_id == business_id,
            ApprovalGrant.revoked_at.is_(None),
            (ApprovalGrant.expires_at.is_(None) | (ApprovalGrant.expires_at > now)),
        ).order_by(ApprovalGrant.created_at.desc()))
        for grant in result.scalars():
            if grant.scope == 'always' or platform in grant.allowed_platforms or not grant.allowed_platforms:
                if content_type in grant.allowed_content_types or not grant.allowed_content_types:
                    return grant
        return None
