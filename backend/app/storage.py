from __future__ import annotations
import json, sqlite3
from contextlib import contextmanager
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__import__("os").environ.get("REACTIVATE_DB_PATH", str(Path(__file__).resolve().parent.parent / "reactivate.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

@contextmanager
def _connect(path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db(path: Path = DB_PATH) -> None:
    with _connect(path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT, dedupe_key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL, city TEXT NOT NULL, category TEXT NOT NULL,
            score REAL NOT NULL, grade TEXT NOT NULL, social_gap_score REAL NOT NULL,
            health_score REAL NOT NULL, radar_json TEXT NOT NULL,
            first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL,
            scan_count INTEGER NOT NULL DEFAULT 1,
            qualification_status TEXT NOT NULL DEFAULT 'UNQUALIFIED',
            priority TEXT NOT NULL DEFAULT 'NORMAL',
            contact_status TEXT NOT NULL DEFAULT 'NOT_CONTACTED',
            notes TEXT NOT NULL DEFAULT '', next_action TEXT NOT NULL DEFAULT ''
        )""")
        # Safe migration for v0.10 databases.
        cols = {r[1] for r in conn.execute("PRAGMA table_info(prospects)").fetchall()}
        migrations = {
            "qualification_status": "ALTER TABLE prospects ADD COLUMN qualification_status TEXT NOT NULL DEFAULT 'UNQUALIFIED'",
            "priority": "ALTER TABLE prospects ADD COLUMN priority TEXT NOT NULL DEFAULT 'NORMAL'",
            "contact_status": "ALTER TABLE prospects ADD COLUMN contact_status TEXT NOT NULL DEFAULT 'NOT_CONTACTED'",
            "notes": "ALTER TABLE prospects ADD COLUMN notes TEXT NOT NULL DEFAULT ''",
            "next_action": "ALTER TABLE prospects ADD COLUMN next_action TEXT NOT NULL DEFAULT ''",
            "outreach_channel": "ALTER TABLE prospects ADD COLUMN outreach_channel TEXT NOT NULL DEFAULT ''",
            "outreach_draft": "ALTER TABLE prospects ADD COLUMN outreach_draft TEXT NOT NULL DEFAULT ''",
            "follow_up_at": "ALTER TABLE prospects ADD COLUMN follow_up_at TEXT NOT NULL DEFAULT ''",
            "contacted_at": "ALTER TABLE prospects ADD COLUMN contacted_at TEXT NOT NULL DEFAULT ''",
        }
        for col, sql in migrations.items():
            if col not in cols: conn.execute(sql)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prospects_score ON prospects(score DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prospects_city ON prospects(city)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(qualification_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prospects_priority ON prospects(priority)")
        conn.execute("""CREATE TABLE IF NOT EXISTS patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, source_url TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL DEFAULT 'URL', transcript TEXT NOT NULL DEFAULT '', hook TEXT NOT NULL DEFAULT '',
            promise TEXT NOT NULL DEFAULT '', structure TEXT NOT NULL DEFAULT '', cta TEXT NOT NULL DEFAULT '',
            angle TEXT NOT NULL DEFAULT '', audience TEXT NOT NULL DEFAULT '', format TEXT NOT NULL DEFAULT '',
            emotional_trigger TEXT NOT NULL DEFAULT '', tags_json TEXT NOT NULL DEFAULT '[]', notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_title ON patterns(title)")
        conn.execute("""CREATE TABLE IF NOT EXISTS content_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, prospect_id INTEGER NOT NULL, type TEXT NOT NULL, title TEXT NOT NULL,
            hook TEXT NOT NULL DEFAULT '', script TEXT NOT NULL DEFAULT '', caption TEXT NOT NULL DEFAULT '', cta TEXT NOT NULL DEFAULT '',
            pattern_source TEXT NOT NULL DEFAULT '', verification_state TEXT NOT NULL DEFAULT 'DRAFT', notes TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'DRAFT', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_content_assets_prospect ON content_assets(prospect_id)")
        conn.execute("""CREATE TABLE IF NOT EXISTS production_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, prospect_id INTEGER NOT NULL, content_asset_id INTEGER NOT NULL,
            production_type TEXT NOT NULL, platform TEXT NOT NULL, aspect_ratio TEXT NOT NULL, duration_seconds INTEGER NOT NULL,
            title TEXT NOT NULL, hook TEXT NOT NULL DEFAULT '', voiceover TEXT NOT NULL DEFAULT '', cta TEXT NOT NULL DEFAULT '',
            shot_list_json TEXT NOT NULL DEFAULT '[]', b_roll_json TEXT NOT NULL DEFAULT '[]', on_screen_text_json TEXT NOT NULL DEFAULT '[]',
            verification_state TEXT NOT NULL DEFAULT 'DRAFT', production_notes TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'BRIEF_READY',
            media_url TEXT NOT NULL DEFAULT '', renderer TEXT NOT NULL DEFAULT '', render_error TEXT NOT NULL DEFAULT '',
            rendered_at TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        # Safe migration for v0.19 renderer metadata.
        prod_cols = {r[1] for r in conn.execute("PRAGMA table_info(production_jobs)").fetchall()}
        prod_migrations = {
            "renderer": "ALTER TABLE production_jobs ADD COLUMN renderer TEXT NOT NULL DEFAULT ''",
            "render_error": "ALTER TABLE production_jobs ADD COLUMN render_error TEXT NOT NULL DEFAULT ''",
            "rendered_at": "ALTER TABLE production_jobs ADD COLUMN rendered_at TEXT NOT NULL DEFAULT ''",
            "provider_task_id": "ALTER TABLE production_jobs ADD COLUMN provider_task_id TEXT NOT NULL DEFAULT ''",
            "provider_model": "ALTER TABLE production_jobs ADD COLUMN provider_model TEXT NOT NULL DEFAULT ''",
        }
        for col, sql in prod_migrations.items():
            if col not in prod_cols: conn.execute(sql)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_production_jobs_prospect ON production_jobs(prospect_id)")
        from .publishing import init_publishing_db
        init_publishing_db(path)
        from .campaigns import init_campaign_db
        init_campaign_db(path)
        from .performance import init_performance_db
        init_performance_db(path)
        from .outreach_events import init_outreach_events_db
        init_outreach_events_db(path)
        from .revenue import init_revenue_db
        init_revenue_db(path)
        from .crm import init_crm_db
        init_crm_db(path)
        from .scheduler import init_scheduler_db
        init_scheduler_db(path)

def _key(record: dict[str, Any]) -> str:
    return (str(record.get("google_url") or record.get("website") or record.get("name", "")).strip().lower())

def upsert_prospect(record: dict[str, Any], path: Path = DB_PATH) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    key = _key(record)
    with _connect(path) as conn:
        existing = conn.execute("SELECT * FROM prospects WHERE dedupe_key=?", (key,)).fetchone()
        if existing:
            # Qualification fields belong to the seller and survive rescans.
            conn.execute("""UPDATE prospects SET name=?,city=?,category=?,score=?,grade=?,social_gap_score=?,health_score=?,radar_json=?,last_seen_at=?,scan_count=? WHERE dedupe_key=?""",
                (record["name"],record["city"],record["category"],record["score"],record["grade"],record["social_gap_score"],record["health_score"],json.dumps(record),now,existing["scan_count"]+1,key))
            prospect_id, first_seen, count = existing["id"], existing["first_seen_at"], existing["scan_count"]+1
            qual = {k: existing[k] for k in ("qualification_status","priority","contact_status","notes","next_action","outreach_channel","outreach_draft","follow_up_at","contacted_at")}
        else:
            cur = conn.execute("""INSERT INTO prospects (dedupe_key,name,city,category,score,grade,social_gap_score,health_score,radar_json,first_seen_at,last_seen_at,scan_count) VALUES (?,?,?,?,?,?,?,?,?,?,?,1)""",
                (key,record["name"],record["city"],record["category"],record["score"],record["grade"],record["social_gap_score"],record["health_score"],json.dumps(record),now,now))
            prospect_id, first_seen, count = cur.lastrowid, now, 1
            qual = {"qualification_status":"UNQUALIFIED","priority":"NORMAL","contact_status":"NOT_CONTACTED","notes":"","next_action":"","outreach_channel":"","outreach_draft":"","follow_up_at":"","contacted_at":""}
    return {"id": prospect_id,"first_seen_at": first_seen,"last_seen_at": now,"scan_count": count,**qual,**record}

def upsert_many(records: list[dict[str, Any]], path: Path = DB_PATH) -> list[dict[str, Any]]:
    return [upsert_prospect(r,path) for r in records]

def _row_to_item(row: sqlite3.Row) -> dict[str, Any]:
    item=json.loads(row["radar_json"])
    item.update({"id":row["id"],"first_seen_at":row["first_seen_at"],"last_seen_at":row["last_seen_at"],"scan_count":row["scan_count"],
                 "qualification_status":row["qualification_status"],"priority":row["priority"],"contact_status":row["contact_status"],"notes":row["notes"],"next_action":row["next_action"],"outreach_channel":row["outreach_channel"],"outreach_draft":row["outreach_draft"],"follow_up_at":row["follow_up_at"],"contacted_at":row["contacted_at"]})
    return item

def list_prospects(path: Path = DB_PATH, *, search: str="", city: str="", min_score: float=0, status: str="", priority: str="", limit: int=100) -> list[dict[str, Any]]:
    clauses,args=["score >= ?"],[min_score]
    if search:
        s=f"%{search.lower()}%"; clauses.append("(LOWER(name) LIKE ? OR LOWER(category) LIKE ?)"); args.extend([s,s])
    if city: clauses.append("LOWER(city) LIKE ?"); args.append(f"%{city.lower()}%")
    if status: clauses.append("qualification_status=?"); args.append(status)
    if priority: clauses.append("priority=?"); args.append(priority)
    args.append(limit)
    with _connect(path) as conn: rows=conn.execute(f"SELECT * FROM prospects WHERE {' AND '.join(clauses)} ORDER BY CASE priority WHEN 'HOT' THEN 0 WHEN 'HIGH' THEN 1 WHEN 'NORMAL' THEN 2 WHEN 'LOW' THEN 3 ELSE 4 END, score DESC, last_seen_at DESC LIMIT ?",args).fetchall()
    return [_row_to_item(r) for r in rows]

def get_prospect(prospect_id:int,path:Path=DB_PATH)->dict[str,Any]|None:
    with _connect(path) as conn: row=conn.execute("SELECT * FROM prospects WHERE id=?",(prospect_id,)).fetchone()
    return _row_to_item(row) if row else None

def update_qualification(prospect_id:int, updates:dict[str,Any], path:Path=DB_PATH)->dict[str,Any]|None:
    allowed={"qualification_status","priority","contact_status","notes","next_action","outreach_channel","outreach_draft","follow_up_at","contacted_at"}
    clean={k:v for k,v in updates.items() if k in allowed and v is not None}
    if not clean: return get_prospect(prospect_id,path)
    with _connect(path) as conn:
        row=conn.execute("SELECT * FROM prospects WHERE id=?",(prospect_id,)).fetchone()
        if not row: return None
        sets=", ".join(f"{k}=?" for k in clean); conn.execute(f"UPDATE prospects SET {sets} WHERE id=?",(*clean.values(),prospect_id))
    return get_prospect(prospect_id,path)


def create_pattern(record: dict[str, Any], path: Path = DB_PATH) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    fields = ["title","source_url","source_type","transcript","hook","promise","structure","cta","angle","audience","format","emotional_trigger","tags","notes"]
    values = [record.get(k, "") if k != "tags" else record.get(k, []) for k in fields]
    with _connect(path) as conn:
        cur = conn.execute("""INSERT INTO patterns (title,source_url,source_type,transcript,hook,promise,structure,cta,angle,audience,format,emotional_trigger,tags_json,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (*values[:12], json.dumps(values[12]), values[13], now))
        pid = cur.lastrowid
    return get_pattern(pid, path)

def list_patterns(path: Path = DB_PATH, search: str = "", limit: int = 100) -> list[dict[str, Any]]:
    clauses=[]; args=[]
    if search:
        clauses.append("(LOWER(title) LIKE ? OR LOWER(tags_json) LIKE ? OR LOWER(angle) LIKE ?)")
        q=f"%{search.lower()}%"; args.extend([q,q,q])
    args.append(limit)
    where=f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with _connect(path) as conn:
        rows=conn.execute(f"SELECT * FROM patterns{where} ORDER BY created_at DESC LIMIT ?", args).fetchall()
    return [_pattern_row(r) for r in rows]

def get_pattern(pattern_id: int, path: Path = DB_PATH) -> dict[str, Any] | None:
    with _connect(path) as conn:
        row=conn.execute("SELECT * FROM patterns WHERE id=?", (pattern_id,)).fetchone()
    return _pattern_row(row) if row else None

def _pattern_row(row: sqlite3.Row) -> dict[str, Any]:
    item=dict(row)
    item["tags"]=json.loads(item.pop("tags_json") or "[]")
    return item


def create_content_assets(prospect_id: int, assets: list[dict[str, Any]], path: Path = DB_PATH) -> list[dict[str, Any]]:
    now=datetime.now(timezone.utc).isoformat()
    created=[]
    with _connect(path) as conn:
        for a in assets:
            cur=conn.execute("""INSERT INTO content_assets (prospect_id,type,title,hook,script,caption,cta,pattern_source,verification_state,notes,status,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", (prospect_id,a.get('type','POST'),a.get('title','Untitled'),a.get('hook',''),a.get('script',''),a.get('caption',''),a.get('cta',''),a.get('pattern_source',''),a.get('verification_state','DRAFT'),a.get('notes',''),'DRAFT',now,now))
            created.append(cur.lastrowid)
    return [get_content_asset(i,path) for i in created]

def get_content_asset(asset_id:int,path:Path=DB_PATH)->dict[str,Any]|None:
    with _connect(path) as conn: row=conn.execute("SELECT * FROM content_assets WHERE id=?",(asset_id,)).fetchone()
    return dict(row) if row else None

def list_content_assets(prospect_id:int,path:Path=DB_PATH,limit:int=50)->list[dict[str,Any]]:
    with _connect(path) as conn: rows=conn.execute("SELECT * FROM content_assets WHERE prospect_id=? ORDER BY created_at DESC LIMIT ?",(prospect_id,limit)).fetchall()
    return [dict(r) for r in rows]

def update_content_asset(asset_id:int,updates:dict[str,Any],path:Path=DB_PATH)->dict[str,Any]|None:
    allowed={'title','hook','script','caption','cta','status','notes'}
    clean={k:v for k,v in updates.items() if k in allowed}
    if not clean: return get_content_asset(asset_id,path)
    clean['updated_at']=datetime.now(timezone.utc).isoformat()
    with _connect(path) as conn:
        if not conn.execute("SELECT 1 FROM content_assets WHERE id=?",(asset_id,)).fetchone(): return None
        sets=", ".join(f"{k}=?" for k in clean); conn.execute(f"UPDATE content_assets SET {sets} WHERE id=?",(*clean.values(),asset_id))
    return get_content_asset(asset_id,path)


def create_production_job(prospect_id:int, content_asset_id:int, brief:dict[str,Any], path:Path=DB_PATH)->dict[str,Any]:
    now=datetime.now(timezone.utc).isoformat()
    with _connect(path) as conn:
        cur=conn.execute("""INSERT INTO production_jobs (prospect_id,content_asset_id,production_type,platform,aspect_ratio,duration_seconds,title,hook,voiceover,cta,shot_list_json,b_roll_json,on_screen_text_json,verification_state,production_notes,status,media_url,renderer,render_error,rendered_at,provider_task_id,provider_model,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(prospect_id,content_asset_id,brief.get('production_type','UGC_VIDEO'),brief.get('platform','INSTAGRAM_REELS'),brief.get('aspect_ratio','9:16'),brief.get('duration_seconds',30),brief.get('title',''),brief.get('hook',''),brief.get('voiceover',''),brief.get('cta',''),json.dumps(brief.get('shot_list',[])),json.dumps(brief.get('b_roll',[])),json.dumps(brief.get('on_screen_text',[])),brief.get('verification_state','DRAFT'),brief.get('production_notes',''),brief.get('status','BRIEF_READY'),brief.get('media_url',''),brief.get('renderer',''),brief.get('render_error',''),brief.get('rendered_at',''),brief.get('provider_task_id',''),brief.get('provider_model',''),now,now))
        jid=cur.lastrowid
    return get_production_job(jid,path)

def get_production_job(job_id:int,path:Path=DB_PATH)->dict[str,Any]|None:
    with _connect(path) as conn: row=conn.execute("SELECT * FROM production_jobs WHERE id=?",(job_id,)).fetchone()
    if not row: return None
    item=dict(row)
    for k in ('shot_list_json','b_roll_json','on_screen_text_json'):
        item[k[:-5]]=json.loads(item.pop(k) or '[]')
    return item

def list_production_jobs(prospect_id:int,path:Path=DB_PATH,limit:int=50)->list[dict[str,Any]]:
    with _connect(path) as conn: rows=conn.execute("SELECT * FROM production_jobs WHERE prospect_id=? ORDER BY created_at DESC LIMIT ?",(prospect_id,limit)).fetchall()
    return [get_production_job(r['id'],path) for r in rows]

def update_production_job(job_id:int,updates:dict[str,Any],path:Path=DB_PATH)->dict[str,Any]|None:
    allowed={'status','media_url','production_notes','platform','aspect_ratio','duration_seconds','renderer','render_error','rendered_at','provider_task_id','provider_model'}
    clean={k:v for k,v in updates.items() if k in allowed and v is not None}
    if not clean: return get_production_job(job_id,path)
    clean['updated_at']=datetime.now(timezone.utc).isoformat()
    with _connect(path) as conn:
        if not conn.execute("SELECT 1 FROM production_jobs WHERE id=?",(job_id,)).fetchone(): return None
        sets=", ".join(f"{k}=?" for k in clean); conn.execute(f"UPDATE production_jobs SET {sets} WHERE id=?",(*clean.values(),job_id))
    return get_production_job(job_id,path)
