from __future__ import annotations

import argparse
import asyncio
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.zernio import ZernioAdapter
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models import GeneratedAsset, MediaAsset, PublishingJob, SocialAccount
from app.services.storage import S3Storage

log = logging.getLogger("nahalabs.publishing_worker")
settings = get_settings()
logging.basicConfig(level=settings.log_level)

MAX_ATTEMPTS = 3
RETRY_SECONDS = (30, 300, 1800)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _obj_value(obj, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _post_id(result) -> str | None:
    post = _obj_value(result, "post")
    if post is None:
        return None
    return _obj_value(post, "_id") or _obj_value(post, "id")


def _post_status(result) -> str | None:
    post = _obj_value(result, "post")
    return _obj_value(post, "status") if post else None


def _next_attempt(attempts: int) -> datetime:
    idx = min(max(attempts - 1, 0), len(RETRY_SECONDS) - 1)
    from datetime import timedelta
    return _now() + timedelta(seconds=RETRY_SECONDS[idx])


async def claim_jobs(db: AsyncSession, limit: int = 10) -> list[PublishingJob]:
    now = _now()
    result = await db.execute(
        select(PublishingJob)
        .where(
            or_(
                (PublishingJob.status == "queued")
                & PublishingJob.approved_at.is_not(None)
                & (PublishingJob.preflight_status == "passed"),
                (PublishingJob.status == "retrying")
                & (PublishingJob.payload["next_attempt_at"].astext <= now.isoformat()),
                (PublishingJob.status == "scheduled")
                & (PublishingJob.external_post_id.is_(None))
                & PublishingJob.approved_at.is_not(None)
                & (PublishingJob.preflight_status == 'passed'),
            )
        )
        .order_by(PublishingJob.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    jobs = list(result.scalars())
    for job in jobs:
        job.status = "publishing"
        job.attempts += 1
    await db.commit()
    return jobs


async def execute_job(db: AsyncSession, job: PublishingJob, adapter: ZernioAdapter, storage: S3Storage) -> None:
    account = await db.get(SocialAccount, job.social_account_id)
    asset = await db.get(GeneratedAsset, job.generated_asset_id)
    if not account or account.status != "connected":
        raise RuntimeError("Social account is not connected")
    if not asset or not asset.media_asset_id:
        raise RuntimeError("Generated asset has no media asset")
    media = await db.get(MediaAsset, asset.media_asset_id)
    if not media:
        raise RuntimeError("Generated media asset not found")

    payload = job.payload or {}
    caption = payload.get("caption") or ""
    custom_content = payload.get("custom_content", {}).get(job.platform) if isinstance(payload.get("custom_content"), dict) else None
    scheduled_for = job.scheduled_at.astimezone(timezone.utc).isoformat() if job.scheduled_at else None
    publish_now = job.scheduled_at is None or job.scheduled_at <= _now()
    if publish_now:
        scheduled_for = None

    with tempfile.TemporaryDirectory(prefix="nahalabs-publish-") as td:
        local = str(Path(td) / Path(media.storage_key).name)
        storage.download(media.storage_key, local)
        media_url = await asyncio.to_thread(adapter.upload_media, local)
        result = await asyncio.to_thread(
            adapter.create_post,
            content=caption,
            account_id=account.external_account_id,
            platform=job.platform,
            media_url=media_url,
            media_type="image" if media.mime_type.startswith("image/") else "video",
            publish_now=publish_now,
            scheduled_for=scheduled_for,
            custom_content=custom_content,
            idempotency_key=job.idempotency_key,
        )

    external_id = _post_id(result)
    if not external_id:
        raise RuntimeError("Zernio did not return a post ID")

    job.external_post_id = str(external_id)
    job.payload = {**payload, "provider_status": _post_status(result)}
    provider_status = _post_status(result)
    if provider_status == "published" and job.scheduled_at is None:
        job.status = "published"
        job.published_at = _now()
    elif job.scheduled_at and not publish_now:
        job.status = "scheduled"
    else:
        job.status = "publishing"
    job.last_error = None
    await db.commit()


async def run_once(limit: int = 10) -> int:
    if not settings.zernio_api_key:
        raise RuntimeError("ZERNIO_API_KEY is required")
    adapter = ZernioAdapter(settings.zernio_api_key, settings.zernio_api_base_url)
    storage = S3Storage()
    async with AsyncSessionLocal() as db:
        jobs = await claim_jobs(db, limit)
        for job in jobs:
            try:
                await execute_job(db, job, adapter, storage)
            except Exception as exc:
                log.exception("Publishing job %s failed", job.id)
                job.last_error = str(exc)[:4000]
                if job.attempts >= MAX_ATTEMPTS:
                    job.status = "failed"
                else:
                    job.status = "retrying"
                    job.payload = {**(job.payload or {}), "next_attempt_at": _next_attempt(job.attempts).isoformat()}
                await db.commit()
        return len(jobs)


async def loop(interval: float = 2.0, batch_size: int = 10) -> None:
    while True:
        processed = await run_once(batch_size)
        if processed == 0:
            await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="NahaLabs Zernio publishing worker")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()
    asyncio.run(run_once(args.batch_size) if args.once else loop(args.interval, args.batch_size))


if __name__ == "__main__":
    main()
