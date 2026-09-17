from __future__ import annotations
import argparse
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from .scheduler import cron_matches, list_scheduled_jobs, run_job
from .storage import DB_PATH, init_db


def run_due_jobs(path: Path = DB_PATH, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(ZoneInfo("Africa/Johannesburg"))
    results = []
    for job in list_scheduled_jobs(path):
        if not job["enabled"]:
            continue
        tz = ZoneInfo(job["timezone"])
        local_now = now.astimezone(tz) if now.tzinfo else now.replace(tzinfo=tz)
        # Avoid duplicate execution inside the same minute.
        if job["last_run_at"]:
            try:
                last = datetime.fromisoformat(job["last_run_at"])\
                    .astimezone(tz)
                if last.replace(second=0, microsecond=0) == local_now.replace(second=0, microsecond=0):
                    continue
            except ValueError:
                pass
        if cron_matches(local_now, job["cron"]):
            try:
                results.append({"job_id": job["id"], "name": job["name"], "status": "SUCCEEDED", "run": run_job(job["id"], path, now)})
            except Exception as exc:
                results.append({"job_id": job["id"], "name": job["name"], "status": "FAILED", "error": str(exc)})
    return results


def worker_loop(path: Path = DB_PATH, interval_seconds: int = 30) -> None:
    init_db(path)
    print(f"Reactivate autonomous worker running; database={path}; interval={interval_seconds}s", flush=True)
    while True:
        try:
            results = run_due_jobs(path)
            for result in results:
                print(result, flush=True)
        except Exception as exc:
            print({"worker_error": str(exc)}, flush=True)
        time.sleep(max(5, interval_seconds))


def main() -> None:
    parser = argparse.ArgumentParser(description="NahaLabs Reactivate autonomous scheduler worker")
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--once", action="store_true", help="Run due jobs once and exit")
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()
    path = Path(args.db)
    init_db(path)
    if args.once:
        print(run_due_jobs(path))
    else:
        worker_loop(path, args.interval)


if __name__ == "__main__":
    main()
