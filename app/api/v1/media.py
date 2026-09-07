import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Business, MediaAsset, SourceMedia, User
from app.schemas.common import UploadCompleteOut, UploadCreate, UploadOut
from app.services.queue import JobQueue
from app.services.storage import S3Storage
from app.services.tenant import require_membership

router = APIRouter(prefix='/media', tags=['media'])


@router.post('/uploads', response_model=UploadOut, status_code=201)
async def create_upload(payload: UploadCreate, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    settings = get_settings()
    if payload.size_bytes > settings.max_upload_bytes:
        raise HTTPException(413, 'File exceeds maximum upload size')
    allowed = set(settings.allowed_video_mime_types + settings.allowed_image_mime_types)
    if payload.mime_type not in allowed:
        raise HTTPException(415, 'Unsupported media type')
    business = await db.get(Business, payload.business_id)
    if not business:
        raise HTTPException(404, 'Business not found')
    await require_membership(db, user.id, business.organization_id)

    asset_id = uuid.uuid4()
    storage = S3Storage()
    key = storage.object_key(business.id, asset_id, payload.filename)
    asset = MediaAsset(id=asset_id, business_id=business.id, type=payload.asset_type, storage_key=key, mime_type=payload.mime_type, size_bytes=payload.size_bytes)
    db.add(asset)
    await db.commit()
    return UploadOut(asset_id=asset_id, storage_key=key, upload_url=storage.presigned_put(key, payload.mime_type), expires_in=settings.aws_s3_upload_expiry_seconds)


@router.post('/{asset_id}/complete', response_model=UploadCompleteOut)
async def complete_upload(asset_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    asset = await db.get(MediaAsset, uuid.UUID(asset_id))
    if not asset:
        raise HTTPException(404, 'Media asset not found')
    business = await db.get(Business, asset.business_id)
    await require_membership(db, user.id, business.organization_id)
    try:
        head = S3Storage().head(asset.storage_key)
    except Exception as exc:
        raise HTTPException(409, 'Upload not found in object storage') from exc
    asset.size_bytes = int(head.get('ContentLength', asset.size_bytes or 0))
    source = SourceMedia(business_id=business.id, media_asset_id=asset.id, status='queued')
    db.add(source)
    await db.commit()
    await db.refresh(source)
    JobQueue().enqueue_media({'job_type': 'media.analyze', 'source_media_id': str(source.id), 'business_id': str(business.id), 'asset_id': str(asset.id)})
    return UploadCompleteOut(source_media_id=source.id, status=source.status)
