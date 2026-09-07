import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Business, ContentPack, CreativeBrief, GeneratedAsset, SourceMedia, User
from app.schemas.generation import CreativeBriefOut, GenerateAssetRequest, GeneratedAssetOut
from app.services.tenant import require_membership
from app.services.queue import JobQueue

router = APIRouter(prefix='/content-packs', tags=['generation'])

@router.get('/{pack_id}/briefs', response_model=list[CreativeBriefOut])
async def list_briefs(pack_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    pack = await db.get(ContentPack, uuid.UUID(pack_id))
    if not pack: raise HTTPException(404, 'Content pack not found')
    business = await db.get(Business, pack.business_id)
    await require_membership(db, user.id, business.organization_id)
    result = await db.execute(select(CreativeBrief).where(CreativeBrief.content_pack_id == pack.id).order_by(CreativeBrief.created_at))
    return list(result.scalars().all())

@router.post('/{pack_id}/briefs/{brief_id}/generate', response_model=GeneratedAssetOut, status_code=202)
async def generate_asset(pack_id: str, brief_id: str, payload: GenerateAssetRequest, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    pack = await db.get(ContentPack, uuid.UUID(pack_id))
    brief = await db.get(CreativeBrief, uuid.UUID(brief_id))
    if not pack or not brief or brief.content_pack_id != pack.id: raise HTTPException(404, 'Creative brief not found')
    business = await db.get(Business, pack.business_id)
    await require_membership(db, user.id, business.organization_id)
    asset = GeneratedAsset(content_pack_id=pack.id, creative_brief_id=brief.id, asset_type=payload.asset_type, status='queued', generation_provider=payload.provider, asset_metadata={'aspect_ratio': payload.aspect_ratio, 'polish_requested': payload.polish_requested, 'polish_prompt': payload.polish_prompt})
    db.add(asset)
    brief.status = 'generating'
    await db.commit(); await db.refresh(asset)
    JobQueue().enqueue_generation({'job_type':'asset.generate','generated_asset_id':str(asset.id),'creative_brief_id':str(brief.id),'content_pack_id':str(pack.id),'business_id':str(business.id),'provider':payload.provider})
    return asset

@router.get('/{pack_id}/assets', response_model=list[GeneratedAssetOut])
async def list_assets(pack_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    pack = await db.get(ContentPack, uuid.UUID(pack_id))
    if not pack:
        raise HTTPException(404, 'Content pack not found')
    business = await db.get(Business, pack.business_id)
    await require_membership(db, user.id, business.organization_id)
    result = await db.execute(select(GeneratedAsset).where(GeneratedAsset.content_pack_id == pack.id).order_by(GeneratedAsset.created_at))
    return list(result.scalars().all())

@router.post('/{pack_id}/assets/{asset_id}/retry', response_model=GeneratedAssetOut, status_code=202)
async def retry_asset(pack_id: str, asset_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    pack = await db.get(ContentPack, uuid.UUID(pack_id))
    asset = await db.get(GeneratedAsset, uuid.UUID(asset_id))
    if not pack or not asset or asset.content_pack_id != pack.id:
        raise HTTPException(404, 'Generated asset not found')
    business = await db.get(Business, pack.business_id)
    await require_membership(db, user.id, business.organization_id)
    if asset.status not in {'failed', 'cancelled'}:
        raise HTTPException(409, f'Asset cannot be retried from status={asset.status}')
    asset.status = 'queued'
    asset.provider_job_id = None
    asset.asset_metadata = {**(asset.asset_metadata or {}), 'retry_requested': True}
    await db.commit(); await db.refresh(asset)
    JobQueue().enqueue_generation({'job_type':'asset.generate','generated_asset_id':str(asset.id),'creative_brief_id':str(asset.creative_brief_id),'content_pack_id':str(pack.id),'business_id':str(business.id),'provider':asset.generation_provider or 'kie'})
    return asset
