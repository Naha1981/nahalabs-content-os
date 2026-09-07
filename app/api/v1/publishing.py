import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Business, GeneratedAsset, MediaAsset, PublishingJob, SocialAccount, User
from app.schemas.publishing import PublishCreate, PublishingResponse, PreflightResponse, ApprovalActionResponse
from app.services.tenant import require_membership
from app.services.publishing import PublishingService
from app.services.publishing_preflight import run_preflight
from app.services.storage import S3Storage
from app.adapters.zernio import ZernioAdapter
from app.core.config import get_settings

router = APIRouter(prefix='/publishing', tags=['publishing'])

def get_adapter():
    key = get_settings().zernio_api_key
    if not key: raise HTTPException(503, 'Publishing provider is not configured')
    return ZernioAdapter(key)

@router.post('/jobs', response_model=PublishingResponse, status_code=201)
async def create_publish_job(business_id: uuid.UUID, body: PublishCreate, idempotency_key: str | None = Header(default=None, alias='Idempotency-Key'), db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)
    if not idempotency_key: raise HTTPException(400, 'Idempotency-Key is required')
    asset = await db.get(GeneratedAsset, body.generated_asset_id)
    account = await db.get(SocialAccount, body.social_account_id)
    if not asset or not account or account.business_id != business.id or asset.content_pack_id is None: raise HTTPException(404, 'Asset or social account not found')
    if account.status != 'connected': raise HTTPException(409, 'Social account is not connected')
    existing = await db.scalar(__import__('sqlalchemy').select(PublishingJob).where(PublishingJob.idempotency_key == idempotency_key))
    if existing: return PublishingResponse.model_validate(existing, from_attributes=True)
    # Consequential action: require explicit grant for this platform/content type.
    svc = PublishingService(db, get_adapter())
    grant = await svc.active_grant(business.id, account.platform, asset.asset_type)
    if not grant: raise HTTPException(409, 'Publishing approval required')
    status = 'awaiting_preflight'
    job = PublishingJob(business_id=business.id, generated_asset_id=asset.id, social_account_id=account.id, platform=account.platform, status=status, scheduled_at=body.scheduled_at, payload={'caption': body.caption, 'custom_content': body.custom_content or {}, 'approval_grant_id': str(grant.id)}, preflight_status='pending', idempotency_key=idempotency_key)
    db.add(job); await db.commit(); await db.refresh(job)
    return PublishingResponse.model_validate(job, from_attributes=True)

@router.get('/jobs', response_model=list[PublishingResponse])
async def list_jobs(business_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)
    result = await db.execute(__import__('sqlalchemy').select(PublishingJob).where(PublishingJob.business_id == business.id).order_by(PublishingJob.created_at.desc()))
    return [PublishingResponse.model_validate(x, from_attributes=True) for x in result.scalars()]


@router.post('/jobs/{job_id}/preflight', response_model=PreflightResponse)
async def preflight_job(business_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)
    job = await db.get(PublishingJob, job_id)
    if not job or job.business_id != business.id: raise HTTPException(404, 'Publishing job not found')
    if job.status in {'published','cancelled','failed'}: raise HTTPException(409, f'Cannot preflight job in {job.status} state')
    asset = await db.get(GeneratedAsset, job.generated_asset_id)
    account = await db.get(SocialAccount, job.social_account_id)
    if not asset or not asset.media_asset_id or not account: raise HTTPException(404, 'Publishing dependencies not found')
    media = await db.get(MediaAsset, asset.media_asset_id)
    if not media: raise HTTPException(404, 'Media asset not found')
    if asset.status != 'approved_ready': raise HTTPException(409, 'Generated asset has not passed the quality gate')
    try:
        result = await run_preflight(job, asset, media, account, get_adapter(), S3Storage())
    except Exception as exc:
        job.preflight_status = 'error'; job.preflight_result = {'valid': False, 'message': str(exc)[:2000]}
        await db.commit()
        raise HTTPException(502, 'Platform preflight failed') from exc
    job.preflight_status = 'passed' if result['valid'] else 'failed'
    job.preflight_result = result
    if not result['valid']:
        job.status = 'preflight_failed'
    else:
        job.status = 'awaiting_approval'
    await db.commit()
    return PreflightResponse(status=job.preflight_status, **result)


@router.post('/jobs/{job_id}/approve', response_model=ApprovalActionResponse)
async def approve_job(business_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    membership = await require_membership(db, user.id, business.organization_id)
    if membership.role not in {'owner','admin','editor'}: raise HTTPException(403, 'Insufficient permission')
    job = await db.get(PublishingJob, job_id)
    if not job or job.business_id != business.id: raise HTTPException(404, 'Publishing job not found')
    if job.preflight_status != 'passed': raise HTTPException(409, 'Successful platform preflight is required before approval')
    if job.status != 'awaiting_approval': raise HTTPException(409, f'Job is not awaiting approval: {job.status}')
    job.approved_by_user_id = user.id
    job.approved_at = datetime.now(timezone.utc)
    job.status = 'scheduled' if job.scheduled_at and job.scheduled_at > datetime.now(timezone.utc) else 'queued'
    await db.commit(); await db.refresh(job)
    return ApprovalActionResponse(id=job.id, status=job.status, preflight_status=job.preflight_status, approved_at=job.approved_at, published_at=job.published_at, external_post_id=job.external_post_id)


@router.post('/jobs/{job_id}/cancel', response_model=ApprovalActionResponse)
async def cancel_job(business_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    membership = await require_membership(db, user.id, business.organization_id)
    if membership.role not in {'owner','admin','editor'}: raise HTTPException(403, 'Insufficient permission')
    job = await db.get(PublishingJob, job_id)
    if not job or job.business_id != business.id: raise HTTPException(404, 'Publishing job not found')
    if job.status in {'published','cancelled'}: raise HTTPException(409, f'Job is already {job.status}')
    job.status = 'cancelled'
    await db.commit(); await db.refresh(job)
    return ApprovalActionResponse(id=job.id, status=job.status, preflight_status=job.preflight_status, approved_at=job.approved_at, published_at=job.published_at, external_post_id=job.external_post_id)


@router.get('/workspace', response_model=list[PublishingResponse])
async def approval_workspace(business_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)
    result = await db.execute(__import__('sqlalchemy').select(PublishingJob).where(PublishingJob.business_id == business.id, PublishingJob.status.in_(['awaiting_preflight','preflight_failed','awaiting_approval','scheduled','queued'])).order_by(PublishingJob.created_at.desc()))
    return [PublishingResponse.model_validate(x, from_attributes=True) for x in result.scalars()]

@router.get('/jobs/{job_id}/provider-status')
async def provider_status(business_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)
    job = await db.get(PublishingJob, job_id)
    if not job or job.business_id != business.id: raise HTTPException(404, 'Publishing job not found')
    return {'job_id': str(job.id), 'status': job.status, 'provider_status': job.provider_status, 'external_post_id': job.external_post_id, 'provider_synced_at': job.provider_synced_at, 'provider_payload': job.provider_payload}

@router.post('/jobs/{job_id}/cancel-provider', response_model=ApprovalActionResponse)
async def cancel_provider_job(business_id: uuid.UUID, job_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    business = await db.get(Business, business_id)
    if not business: raise HTTPException(404, 'Business not found')
    membership = await require_membership(db, user.id, business.organization_id)
    if membership.role not in {'owner','admin','editor'}: raise HTTPException(403, 'Insufficient permission')
    job = await db.get(PublishingJob, job_id)
    if not job or job.business_id != business.id: raise HTTPException(404, 'Publishing job not found')
    if not job.external_post_id:
        job.status = 'cancelled'
    elif job.provider_status == 'published' or job.status == 'published':
        raise HTTPException(409, 'Published posts cannot be cancelled; use the provider unpublish flow where supported')
    else:
        try:
            get_adapter().delete_post(job.external_post_id)
            job.status = 'cancelled'
            job.provider_status = 'cancelled'
            job.provider_synced_at = datetime.now(timezone.utc)
        except Exception as exc:
            raise HTTPException(502, 'Provider cancellation failed') from exc
    await db.commit(); await db.refresh(job)
    return ApprovalActionResponse(id=job.id, status=job.status, preflight_status=job.preflight_status, approved_at=job.approved_at, published_at=job.published_at, external_post_id=job.external_post_id)
