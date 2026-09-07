import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Business, SocialAccount, User
from app.services.tenant import require_membership
from app.adapters.zernio import ZernioAdapter
from app.services.publishing import PublishingService
from app.schemas.publishing import ConnectURLResponse, SocialAccountResponse

router = APIRouter(prefix='/social', tags=['social'])

def adapter() -> ZernioAdapter:
    settings = get_settings()
    if not settings.zernio_api_key:
        raise HTTPException(503, 'Publishing provider is not configured')
    return ZernioAdapter(settings.zernio_api_key)

@router.get('/connect-url', response_model=ConnectURLResponse)
async def get_connect_url(business_id: uuid.UUID, platform: str = Query(..., min_length=2), db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)
    svc = PublishingService(db, adapter())
    profile = await svc.ensure_profile(business)
    await db.commit()
    return ConnectURLResponse(platform=platform, profile_id=profile.external_profile_id, auth_url=svc.adapter.connect_url(platform, profile.external_profile_id))

@router.get('/accounts', response_model=list[SocialAccountResponse])
async def list_accounts(business_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)
    result = await db.execute(select(SocialAccount).where(SocialAccount.business_id == business.id, SocialAccount.status == 'connected'))
    return [SocialAccountResponse(id=a.id, platform=a.platform, username=a.username, display_name=a.display_name, status=a.status) for a in result.scalars()]
