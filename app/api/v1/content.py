import uuid
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Business, ContentPack, GenerationJob, SourceMedia, User
from app.schemas.common import ContentPackCreate, ContentPackOut, JobOut
from app.services.queue import JobQueue
from app.services.tenant import require_membership

router = APIRouter(prefix='/content-packs', tags=['content'])


@router.post('', response_model=ContentPackOut, status_code=201)
async def create_pack(payload: ContentPackCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, payload.business_id)
    if not business:
        raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)
    source = await db.get(SourceMedia, payload.source_media_id)
    if not source or source.business_id != business.id:
        raise HTTPException(404, 'Source media not found')
    pack = ContentPack(
        business_id=business.id,
        name=payload.name,
        source_media_id=source.id,
        status='draft',
        strategy={'objective': payload.objective, 'platforms': payload.platforms, 'asset_target': payload.asset_target},
    )
    db.add(pack)
    await db.commit()
    await db.refresh(pack)
    return pack


@router.get('', response_model=list[ContentPackOut])
async def list_packs(business_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, uuid.UUID(business_id))
    if not business:
        raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)
    result = await db.execute(select(ContentPack).where(ContentPack.business_id == business.id).order_by(ContentPack.created_at.desc()))
    return list(result.scalars().all())


@router.post('/{pack_id}/generate', response_model=JobOut, status_code=202)
async def generate_pack(pack_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user), idempotency_key: str | None = Header(default=None, alias='Idempotency-Key')):
    pack = await db.get(ContentPack, uuid.UUID(pack_id))
    if not pack:
        raise HTTPException(404, 'Content pack not found')
    business = await db.get(Business, pack.business_id)
    await require_membership(db, user.id, business.organization_id)
    if idempotency_key:
        existing = await db.scalar(select(GenerationJob).where(GenerationJob.idempotency_key == idempotency_key))
        if existing:
            return existing
    job = GenerationJob(
        business_id=business.id,
        content_pack_id=pack.id,
        job_type='content_pack.generate',
        status='queued',
        payload={'content_pack_id': str(pack.id), 'source_media_id': str(pack.source_media_id), 'strategy': pack.strategy},
        idempotency_key=idempotency_key,
    )
    pack.status = 'generating'
    db.add(job)
    await db.commit()
    await db.refresh(job)
    JobQueue().enqueue_generation({'job_id': str(job.id), 'job_type': job.job_type, 'business_id': str(business.id), 'content_pack_id': str(pack.id)})
    return job
