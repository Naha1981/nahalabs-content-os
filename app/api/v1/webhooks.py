import hashlib, hmac, json, uuid
from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models import WebhookEvent, SocialAccount, PublishingJob
from sqlalchemy import select
from datetime import datetime, timezone

router = APIRouter(prefix='/webhooks', tags=['webhooks'])

def verify_signature(raw: bytes, signature: str | None, secret: str | None) -> bool:
    if not secret or not signature: return False
    candidate = signature.removeprefix('sha256=')
    digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, candidate)

def extract_event(payload: dict):
    event_id = payload.get('id') or payload.get('eventId') or payload.get('event_id')
    event_type = payload.get('type') or payload.get('event') or payload.get('eventType')
    data = payload.get('data') or payload.get('payload') or payload
    return str(event_id) if event_id else None, event_type, data

@router.post('/zernio', status_code=202)
async def zernio_webhook(request: Request, x_zernio_signature: str | None = Header(default=None)):
    settings = get_settings(); raw = await request.body()
    if not verify_signature(raw, x_zernio_signature, settings.zernio_webhook_secret): raise HTTPException(401, 'Invalid webhook signature')
    try: payload = json.loads(raw)
    except json.JSONDecodeError as exc: raise HTTPException(400, 'Invalid JSON') from exc
    event_id, event_type, data = extract_event(payload)
    if not event_id: raise HTTPException(400, 'Missing event id')
    async with AsyncSessionLocal() as db:
        event = WebhookEvent(provider='zernio', external_event_id=event_id, event_type=event_type, payload=payload)
        db.add(event)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            return {'accepted': True, 'duplicate': True, 'event_id': event_id}
        # Lightweight state projection. Heavy work remains asynchronous in the publishing worker.
        external_post_id = data.get('postId') or data.get('post_id') or data.get('id') if isinstance(data, dict) else None
        if external_post_id:
            job = await db.scalar(select(PublishingJob).where(PublishingJob.external_post_id == str(external_post_id)))
            if job and event_type in {'post.platform.published','post.published'}:
                job.status='published'; job.published_at=datetime.now(timezone.utc)
            elif job and event_type in {'post.platform.failed','post.failed'}:
                job.status='failed'; job.last_error=str(data.get('error') if isinstance(data,dict) else 'Publishing failed')
        event.status='processed'; await db.commit()
    return {'accepted': True, 'duplicate': False, 'event_id': event_id}
