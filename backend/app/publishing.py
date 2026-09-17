from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .storage import DB_PATH, _connect

PLATFORMS={"INSTAGRAM","FACEBOOK","TIKTOK","LINKEDIN","YOUTUBE"}
STATUSES={"QUEUED","SCHEDULED","PUBLISHING","PUBLISHED","FAILED","CANCELLED"}

def init_publishing_db(path:Path=DB_PATH)->None:
    with _connect(path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS publishing_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, production_job_id INTEGER NOT NULL,
            prospect_id INTEGER NOT NULL, platform TEXT NOT NULL, caption TEXT NOT NULL DEFAULT '',
            hashtags_json TEXT NOT NULL DEFAULT '[]', media_url TEXT NOT NULL DEFAULT '',
            scheduled_for TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'QUEUED',
            provider TEXT NOT NULL DEFAULT 'DRY_RUN', published_url TEXT NOT NULL DEFAULT '',
            error TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_publishing_status_time ON publishing_jobs(status,scheduled_for)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_publishing_production ON publishing_jobs(production_job_id)")

def _row(row):
    if not row:return None
    d=dict(row); d['hashtags']=json.loads(d.pop('hashtags_json') or '[]'); return d

def create_publish_job(production_job_id:int, prospect_id:int, platform:str, caption:str, hashtags:list[str], media_url:str, scheduled_for:str='', provider:str='DRY_RUN', path:Path=DB_PATH)->dict:
    platform=platform.upper(); provider=provider.upper()
    if platform not in PLATFORMS: raise ValueError(f"Unsupported platform: {platform}")
    now=datetime.now(timezone.utc).isoformat()
    status='SCHEDULED' if scheduled_for else 'QUEUED'
    with _connect(path) as conn:
        cur=conn.execute("INSERT INTO publishing_jobs (production_job_id,prospect_id,platform,caption,hashtags_json,media_url,scheduled_for,status,provider,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",(production_job_id,prospect_id,platform,caption,json.dumps(hashtags),media_url,scheduled_for,status,provider,now,now))
        job_id=cur.lastrowid
    return get_publish_job(job_id,path)

def get_publish_job(job_id:int,path:Path=DB_PATH):
    with _connect(path) as conn:return _row(conn.execute("SELECT * FROM publishing_jobs WHERE id=?",(job_id,)).fetchone())

def list_publish_jobs(prospect_id:int,path:Path=DB_PATH,limit:int=50):
    with _connect(path) as conn: rows=conn.execute("SELECT * FROM publishing_jobs WHERE prospect_id=? ORDER BY COALESCE(scheduled_for,created_at) DESC LIMIT ?",(prospect_id,limit)).fetchall()
    return [_row(r) for r in rows]

def update_publish_job(job_id:int,updates:dict[str,Any],path:Path=DB_PATH):
    allowed={'caption','hashtags_json','media_url','scheduled_for','status','provider','published_url','error'}
    clean={k:v for k,v in updates.items() if k in allowed and v is not None}
    if 'hashtags' in updates: clean['hashtags_json']=json.dumps(updates['hashtags'])
    clean.pop('hashtags',None)
    if not clean:return get_publish_job(job_id,path)
    clean['updated_at']=datetime.now(timezone.utc).isoformat()
    with _connect(path) as conn:
        if not conn.execute("SELECT 1 FROM publishing_jobs WHERE id=?",(job_id,)).fetchone():return None
        sets=', '.join(f'{k}=?' for k in clean); conn.execute(f'UPDATE publishing_jobs SET {sets} WHERE id=?',(*clean.values(),job_id))
    return get_publish_job(job_id,path)

def dry_run_publish(job:dict[str,Any],path:Path=DB_PATH):
    """Provider-neutral publish simulation. Never contacts a social platform."""
    if job['status'] not in {'QUEUED','SCHEDULED'}: return job
    token=f"dryrun-{job['platform'].lower()}-{job['id']}"
    url=f"https://example.nahalabs.local/published/{token}"
    return update_publish_job(job['id'],{'status':'PUBLISHED','provider':'DRY_RUN','published_url':url,'error':''},path)
