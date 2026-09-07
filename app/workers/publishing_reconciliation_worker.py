from __future__ import annotations
import argparse
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.adapters.zernio import ZernioAdapter
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models import PublishingJob
from app.services.publishing_reconciliation import reconcile_job

settings = get_settings()
log = logging.getLogger("nahalabs.publishing_reconciliation")
logging.basicConfig(level=settings.log_level)

async def run_once(limit: int = 50) -> int:
    if not settings.zernio_api_key:
        raise RuntimeError("ZERNIO_API_KEY is required")
    adapter = ZernioAdapter(settings.zernio_api_key, settings.zernio_api_base_url)
    async with AsyncSessionLocal() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
        result = await db.execute(
            select(PublishingJob).where(
                PublishingJob.external_post_id.is_not(None),
                PublishingJob.provider_synced_at.is_(None) | (PublishingJob.provider_synced_at < cutoff),
                PublishingJob.status.in_(["publishing", "scheduled", "published", "partial", "failed"]),
            ).order_by(PublishingJob.updated_at).limit(limit)
        )
        jobs = list(result.scalars())
        for job in jobs:
            try:
                await reconcile_job(db, job, adapter)
            except Exception as exc:
                job.reconciliation_attempts += 1
                job.last_error = f"reconciliation: {str(exc)[:1500]}"
                await db.commit()
        return len(jobs)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--interval", type=int, default=300)
    args = parser.parse_args()
    while True:
        await run_once()
        if args.once:
            return
        await asyncio.sleep(max(args.interval, 30))

if __name__ == "__main__":
    asyncio.run(main())
