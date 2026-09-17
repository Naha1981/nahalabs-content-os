from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from backend.app.storage import init_db
from backend.app.scheduler import list_scheduled_jobs, cron_matches, next_run_for
from backend.app.worker import run_due_jobs


def test_cron_matching_and_next_run():
    tz = ZoneInfo("Africa/Johannesburg")
    assert cron_matches(datetime(2026, 9, 17, 6, 0, tzinfo=tz), "0 6 * * *")
    assert cron_matches(datetime(2026, 9, 17, 6, 30, tzinfo=tz), "*/15 * * * *")
    assert not cron_matches(datetime(2026, 9, 17, 6, 31, tzinfo=tz), "*/15 * * * *")
    nxt = next_run_for("0 6 * * *", "Africa/Johannesburg", datetime(2026, 9, 17, 6, 1, tzinfo=tz))
    assert nxt.startswith("2026-09-18T06:00:00")


def test_worker_runs_due_job_once_per_minute(tmp_path: Path):
    db = tmp_path / "worker.db"
    init_db(db)
    now = datetime(2026, 9, 17, 6, 0, tzinfo=ZoneInfo("Africa/Johannesburg"))
    out = run_due_jobs(db, now)
    assert any(x["name"] == "Morning Operator" for x in out)
    assert run_due_jobs(db, now) == []


def test_scheduler_has_next_run_times(tmp_path: Path):
    db = tmp_path / "next.db"
    init_db(db)
    jobs = list_scheduled_jobs(db)
    assert all(j["next_run_at"] for j in jobs)
