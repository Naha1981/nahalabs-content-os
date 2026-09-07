import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Business, ContentPack, GeneratedAsset, QualityCheck, User
from app.schemas.quality import QualityCheckOut
from app.services.quality_engine import run_quality_check
from app.services.tenant import require_membership
router=APIRouter(prefix='/quality',tags=['quality'])
@router.post('/assets/{asset_id}/check',response_model=QualityCheckOut)
async def check(asset_id:uuid.UUID,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    asset=await db.get(GeneratedAsset,asset_id)
    if not asset: raise HTTPException(404,'Generated asset not found')
    pack=await db.get(ContentPack,asset.content_pack_id); business=await db.get(Business,pack.business_id)
    await require_membership(db,user.id,business.organization_id)
    if asset.status not in {'quality_review','quality_failed','approved_ready'}: raise HTTPException(409,f'Asset is not ready for quality check: {asset.status}')
    result=await run_quality_check(db,asset); await db.commit(); await db.refresh(result)
    return result
@router.get('/assets/{asset_id}',response_model=list[QualityCheckOut])
async def history(asset_id:uuid.UUID,db:AsyncSession=Depends(get_db),user:User=Depends(current_user)):
    asset=await db.get(GeneratedAsset,asset_id)
    if not asset: raise HTTPException(404,'Generated asset not found')
    pack=await db.get(ContentPack,asset.content_pack_id); business=await db.get(Business,pack.business_id)
    await require_membership(db,user.id,business.organization_id)
    rows=(await db.execute(select(QualityCheck).where(QualityCheck.generated_asset_id==asset_id).order_by(QualityCheck.checked_at.desc()))).scalars().all()
    return list(rows)
