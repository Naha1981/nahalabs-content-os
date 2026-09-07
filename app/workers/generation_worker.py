from __future__ import annotations
import argparse
import asyncio
import logging
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import GeneratedAsset
from app.services.creative_generation import CreativeGenerationOrchestrator
from app.services.quality_engine import run_quality_check

log = logging.getLogger("nahalabs.generation_worker")
logging.basicConfig(level="INFO")

async def run_once() -> dict[str, int]:
    submitted = polled = failed = 0
    orchestrator = CreativeGenerationOrchestrator()
    async with AsyncSessionLocal() as db:
        # with_for_update(skip_locked=True) prevents two concurrent workers (e.g. overlapping
        # SQS-triggered invocations) from both selecting the same "queued" row and both
        # submitting it to the paid generation provider. A second worker's identical locked
        # query simply skips any row already claimed by this transaction.
        queued = (
            await db.execute(
                select(GeneratedAsset)
                .where(GeneratedAsset.status == "queued")
                .limit(25)
                .with_for_update(skip_locked=True)
            )
        ).scalars().all()
        for asset in queued:
            try:
                await orchestrator.submit(db, asset); submitted += 1
            except Exception as exc:
                asset.status = "failed"
                asset.asset_metadata = {**(asset.asset_metadata or {}), "error": str(exc)}
                failed += 1

        # Same reasoning applies to in-flight assets: poll() can issue a second paid provider
        # call (the polish resubmission), so these rows need the same claim protection.
        active = (
            await db.execute(
                select(GeneratedAsset)
                .where(GeneratedAsset.status.in_(["provider_processing", "polishing"]))
                .limit(50)
                .with_for_update(skip_locked=True)
            )
        ).scalars().all()
        for asset in active:
            try:
                result = await orchestrator.poll(db, asset); polled += 1
                if result.get("status") == "quality_review":
                    await run_quality_check(db, asset)
            except Exception as exc:
                asset.status = "failed"
                asset.asset_metadata = {**(asset.asset_metadata or {}), "poll_error": str(exc)}
                failed += 1
        await db.commit()
    return {"submitted": submitted, "polled": polled, "failed": failed}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if not args.once:
        raise SystemExit("Use --once under a scheduler/SQS-triggered deployment.")
    print(asyncio.run(run_once()))

if __name__ == "__main__":
    main()
