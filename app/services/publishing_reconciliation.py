from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.zernio import ZernioAdapter
from app.models import PublishingJob, SocialAccount


def now():
    return datetime.now(timezone.utc)


def value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def extract_post(result):
    return value(result, "post", result if isinstance(result, dict) else None)


def extract_status(result):
    post = extract_post(result)
    return value(post, "status") if post else None

async def reconcile_job(db: AsyncSession, job: PublishingJob, adapter: ZernioAdapter) -> None:
    if not job.external_post_id:
        return
    result = await __import__('asyncio').to_thread(adapter.get_post, job.external_post_id)
    post = extract_post(result)
    status = extract_status(result)
    job.provider_status = status
    job.provider_payload = result if isinstance(result, dict) else {"raw": str(result)}
    job.provider_synced_at = now()
    job.reconciliation_attempts += 1
    if status == "published":
        job.status = "published"
        job.published_at = job.published_at or now()
        job.last_error = None
    elif status in {"failed", "partial"}:
        job.status = status
        job.last_error = value(post, "error") or value(post, "message") or job.last_error
    elif status == "cancelled":
        job.status = "cancelled"
    elif status == "scheduled":
        job.status = "scheduled"
    await db.commit()
