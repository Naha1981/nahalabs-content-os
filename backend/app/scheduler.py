from __future__ import annotations
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any
from .storage import DB_PATH, _connect

JOB_TYPES = {"MORNING_OPERATOR", "RADAR_SCAN", "FOLLOW_UP_CHECK", "CAMPAIGN_CHECK", "PUBLISHING_CHECK", "LEARNING_UPDATE"}
STATUSES = {"ENABLED", "DISABLED"}



def _cron_match_field(value: int, expr: str, minimum: int, maximum: int) -> bool:
    for part in expr.split(","):
        part = part.strip()
        if part == "*":
            return True
        if part.startswith("*/"):
            try:
                step = int(part[2:])
                if step > 0 and (value - minimum) % step == 0:
                    return True
            except ValueError:
                pass
            continue
        try:
            if int(part) == value:
                return True
        except ValueError:
            continue
    return False


def cron_matches(dt: datetime, cron: str) -> bool:
    fields = cron.split()
    if len(fields) != 5:
        return False
    minute, hour, dom, month, dow = fields
    return (
        _cron_match_field(dt.minute, minute, 0, 59) and
        _cron_match_field(dt.hour, hour, 0, 23) and
        _cron_match_field(dt.day, dom, 1, 31) and
        _cron_match_field(dt.month, month, 1, 12) and
        _cron_match_field((dt.weekday() + 1) % 7, dow, 0, 6)
    )


def next_run_for(cron: str, timezone_name: str = "Africa/Johannesburg", after: datetime | None = None) -> str:
    tz = ZoneInfo(timezone_name)
    base = after or datetime.now(tz)
    if base.tzinfo is None:
        base = base.replace(tzinfo=tz)
    else:
        base = base.astimezone(tz)
    candidate = base.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(60 * 24 * 370):
        if cron_matches(candidate, cron):
            return candidate.isoformat()
        candidate += timedelta(minutes=1)
    return ""

def init_scheduler_db(path: Path = DB_PATH) -> None:
    with _connect(path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS scheduled_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
            job_type TEXT NOT NULL, cron TEXT NOT NULL, timezone TEXT NOT NULL DEFAULT 'Africa/Johannesburg',
            enabled INTEGER NOT NULL DEFAULT 1, last_run_at TEXT NOT NULL DEFAULT '',
            next_run_at TEXT NOT NULL DEFAULT '', last_status TEXT NOT NULL DEFAULT 'NEVER_RUN',
            last_result_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS job_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, scheduled_job_id INTEGER NOT NULL,
            job_type TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL, result_json TEXT NOT NULL DEFAULT '{}', error TEXT NOT NULL DEFAULT ''
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_enabled ON scheduled_jobs(enabled)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_job_runs_job ON job_runs(scheduled_job_id,started_at DESC)")
        defaults = [
            ("Morning Operator", "MORNING_OPERATOR", "0 6 * * *"),
            ("Radar Scan", "RADAR_SCAN", "30 6 * * *"),
            ("Follow-up Check", "FOLLOW_UP_CHECK", "0 8,12,16 * * *"),
            ("Campaign Check", "CAMPAIGN_CHECK", "0 * * * *"),
            ("Publishing Check", "PUBLISHING_CHECK", "*/15 * * * *"),
            ("Learning Update", "LEARNING_UPDATE", "0 18 * * *"),
        ]
        now=datetime.now(timezone.utc).isoformat()
        for name,jt,cron in defaults:
            conn.execute("INSERT OR IGNORE INTO scheduled_jobs (name,job_type,cron,created_at,updated_at,next_run_at) VALUES (?,?,?,?,?,?)",(name,jt,cron,now,now,next_run_for(cron, "Africa/Johannesburg")))


def list_scheduled_jobs(path: Path = DB_PATH) -> list[dict[str,Any]]:
    with _connect(path) as conn:
        rows=conn.execute("SELECT * FROM scheduled_jobs ORDER BY id").fetchall()
    out=[]
    for r in rows:
        d=dict(r); d['enabled']=bool(d['enabled'])
        try: d['last_result']=__import__('json').loads(d.pop('last_result_json') or '{}')
        except Exception: d['last_result']={}
        out.append(d)
    return out


def set_job_enabled(job_id:int, enabled:bool, path:Path=DB_PATH):
    now=datetime.now(timezone.utc).isoformat()
    with _connect(path) as conn:
        
        row = conn.execute("SELECT cron,timezone FROM scheduled_jobs WHERE id=?", (job_id,)).fetchone()
        next_run = next_run_for(row["cron"], row["timezone"]) if enabled and row else ""
        conn.execute("UPDATE scheduled_jobs SET enabled=?,next_run_at=?,updated_at=? WHERE id=?",(1 if enabled else 0,next_run,now,job_id))
    return next((x for x in list_scheduled_jobs(path) if x['id']==job_id),None)


def _run_logic(job_type:str, path:Path, now:datetime)->dict[str,Any]:
    if job_type=="MORNING_OPERATOR":
        from .daily_operator import daily_operator
        return daily_operator(path, now)
    if job_type=="FOLLOW_UP_CHECK" or job_type=="CAMPAIGN_CHECK" or job_type=="PUBLISHING_CHECK":
        from .daily_operator import daily_operator
        d=daily_operator(path, now)
        kinds={"FOLLOW_UP_CHECK":{"FOLLOW_UP","DEAL_FOLLOW_UP"},"CAMPAIGN_CHECK":{"CAMPAIGN","APPROVAL","PUBLISH","MEASURE"},"PUBLISHING_CHECK":{"PUBLISH_QUEUE"}}[job_type]
        actions=[a for a in d['actions'] if a['kind'] in kinds]
        return {'generated_at':d['generated_at'],'job_type':job_type,'actions':actions,'total_actions':len(actions)}
    if job_type=="LEARNING_UPDATE":
        from .learning_engine import learning_summary
        return learning_summary(path=path)
    if job_type=="RADAR_SCAN":
        # The external discovery worker is intentionally not invoked without credentials/network.
        return {'job_type':job_type,'status':'READY','note':'Scheduler checkpoint created; external radar discovery remains provider/network gated.'}
    raise ValueError(f"Unsupported job type: {job_type}")


def run_job(job_id:int, path:Path=DB_PATH, now:datetime|None=None)->dict[str,Any]:
    now=now or datetime.now(timezone.utc)
    with _connect(path) as conn:
        row=conn.execute("SELECT * FROM scheduled_jobs WHERE id=?",(job_id,)).fetchone()
        if not row: raise ValueError('Scheduled job not found')
        if not row['enabled']: raise ValueError('Scheduled job is disabled')
        started=now.isoformat()
        cur=conn.execute("INSERT INTO job_runs (scheduled_job_id,job_type,started_at,status) VALUES (?,?,?,?)",(job_id,row['job_type'],started,'RUNNING'))
        run_id=cur.lastrowid
    import json
    try:
        result=_run_logic(row['job_type'],path,now)
        finished=datetime.now(timezone.utc).isoformat()
        with _connect(path) as conn:
            conn.execute("UPDATE job_runs SET finished_at=?,status=?,result_json=? WHERE id=?",(finished,'SUCCEEDED',json.dumps(result),run_id))
            next_run = next_run_for(row["cron"], row["timezone"], now)
            conn.execute("UPDATE scheduled_jobs SET last_run_at=?,last_status=?,last_result_json=?,next_run_at=?,updated_at=? WHERE id=?",(started,'SUCCEEDED',json.dumps(result),next_run,finished,job_id))
        return {'run_id':run_id,'job':next(x for x in list_scheduled_jobs(path) if x['id']==job_id),'result':result}
    except Exception as exc:
        finished=datetime.now(timezone.utc).isoformat()
        with _connect(path) as conn:
            conn.execute("UPDATE job_runs SET finished_at=?,status=?,error=? WHERE id=?",(finished,'FAILED',str(exc),run_id))
            next_run = next_run_for(row["cron"], row["timezone"], now)
            conn.execute("UPDATE scheduled_jobs SET last_run_at=?,last_status=?,last_result_json=?,next_run_at=?,updated_at=? WHERE id=?",(started,'FAILED',json.dumps({'error':str(exc)}),next_run,finished,job_id))
        raise


def list_job_runs(job_id:int|None=None, limit:int=50, path:Path=DB_PATH)->list[dict[str,Any]]:
    with _connect(path) as conn:
        if job_id is None: rows=conn.execute("SELECT * FROM job_runs ORDER BY started_at DESC LIMIT ?",(limit,)).fetchall()
        else: rows=conn.execute("SELECT * FROM job_runs WHERE scheduled_job_id=? ORDER BY started_at DESC LIMIT ?",(job_id,limit)).fetchall()
    import json
    out=[]
    for r in rows:
        d=dict(r)
        try:d['result']=json.loads(d.pop('result_json') or '{}')
        except Exception:d['result']={}
        out.append(d)
    return out


def automation_health(path: Path = DB_PATH) -> dict[str, Any]:
    jobs = list_scheduled_jobs(path)
    runs = list_job_runs(path=path, limit=200)
    enabled = sum(1 for j in jobs if j["enabled"])
    succeeded = sum(1 for r in runs if r["status"] == "SUCCEEDED")
    failed = sum(1 for r in runs if r["status"] == "FAILED")
    never = sum(1 for j in jobs if j["last_status"] == "NEVER_RUN")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jobs_total": len(jobs), "jobs_enabled": enabled, "jobs_disabled": len(jobs)-enabled,
        "runs_sampled": len(runs), "runs_succeeded": succeeded, "runs_failed": failed,
        "jobs_never_run": never,
        "health": "HEALTHY" if failed == 0 else "ATTENTION_REQUIRED",
    }
