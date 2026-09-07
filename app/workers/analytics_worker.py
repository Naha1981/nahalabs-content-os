from __future__ import annotations
import argparse, asyncio, logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.adapters.zernio import ZernioAdapter
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models import ZernioProfile, SocialAccount
from app.services.analytics_learning import ingest_post_analytics, refresh_insights

settings = get_settings()
logging.basicConfig(level=settings.log_level)
log = logging.getLogger("nahalabs.analytics_worker")


def unpack(result):
    if isinstance(result, dict):
        return result.get("posts") or result.get("data") or []
    return getattr(result, "posts", None) or getattr(result, "data", None) or []

async def run_once() -> int:
    if not settings.zernio_api_key:
        raise RuntimeError("ZERNIO_API_KEY is required")
    adapter = ZernioAdapter(settings.zernio_api_key)
    since = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    until = datetime.now(timezone.utc).date().isoformat()
    processed = 0
    async with AsyncSessionLocal() as db:
        profiles = (await db.execute(select(ZernioProfile).where(ZernioProfile.status == "active"))).scalars().all()
        for profile in profiles:
            try:
                result = await asyncio.to_thread(adapter.get_analytics, profile_id=profile.external_profile_id, from_date=since, to_date=until)
                rows = unpack(result)
                processed += await ingest_post_analytics(db, profile.business_id, rows)
                await refresh_insights(db, profile.business_id)
            except Exception:
                log.exception("Analytics sync failed for business %s", profile.business_id)
    return processed

async def loop(interval: float = 900):
    while True:
        await run_once()
        await asyncio.sleep(interval)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true")
    p.add_argument("--interval", type=float, default=900)
    args = p.parse_args()
    asyncio.run(run_once() if args.once else loop(args.interval))

if __name__ == "__main__":
    main()
