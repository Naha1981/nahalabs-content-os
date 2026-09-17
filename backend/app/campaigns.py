from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .storage import DB_PATH, _connect

STATUSES={"PLANNED","CONTENT_READY","AWAITING_APPROVAL","IN_PRODUCTION","READY_TO_PUBLISH","LIVE","MEASURING","COMPLETED","BLOCKED"}
STAGES=("PLAN","CONTENT","APPROVAL","PRODUCTION","PUBLISH","MEASURE")

def init_campaign_db(path:Path=DB_PATH)->None:
    with _connect(path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS campaigns (
          id INTEGER PRIMARY KEY AUTOINCREMENT, prospect_id INTEGER NOT NULL, name TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'PLANNED', stage TEXT NOT NULL DEFAULT 'PLAN',
          objective TEXT NOT NULL DEFAULT 'REACTIVATE_DEMAND', asset_ids_json TEXT NOT NULL DEFAULT '[]',
          production_job_ids_json TEXT NOT NULL DEFAULT '[]', publishing_job_ids_json TEXT NOT NULL DEFAULT '[]',
          next_action TEXT NOT NULL DEFAULT '', blockers_json TEXT NOT NULL DEFAULT '[]',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_prospect ON campaigns(prospect_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status)")

def _row(row):
    if not row:return None
    d=dict(row)
    for k in ('asset_ids_json','production_job_ids_json','publishing_job_ids_json','blockers_json'):
        out=k[:-5] if k.endswith('_json') else k
        d[out]=json.loads(d.pop(k) or '[]')
    return d

def create_campaign(prospect_id:int,name:str,objective:str='REACTIVATE_DEMAND',path:Path=DB_PATH)->dict:
    now=datetime.now(timezone.utc).isoformat()
    with _connect(path) as conn:
        cur=conn.execute("INSERT INTO campaigns(prospect_id,name,objective,created_at,updated_at) VALUES(?,?,?,?,?)",(prospect_id,name,objective,now,now))
        cid=cur.lastrowid
    return get_campaign(cid,path)

def get_campaign(campaign_id:int,path:Path=DB_PATH):
    with _connect(path) as conn:return _row(conn.execute("SELECT * FROM campaigns WHERE id=?",(campaign_id,)).fetchone())

def list_campaigns(prospect_id:int,path:Path=DB_PATH,limit:int=20):
    with _connect(path) as conn: rows=conn.execute("SELECT * FROM campaigns WHERE prospect_id=? ORDER BY created_at DESC LIMIT ?",(prospect_id,limit)).fetchall()
    return [_row(r) for r in rows]


def list_active_campaigns(prospect_id:int,path:Path=DB_PATH)->list[dict]:
    with _connect(path) as conn:
        rows=conn.execute("SELECT * FROM campaigns WHERE prospect_id=? AND status NOT IN ('COMPLETED','BLOCKED') ORDER BY created_at DESC",(prospect_id,)).fetchall()
    return [_row(r) for r in rows]

def update_campaign(campaign_id:int,updates:dict[str,Any],path:Path=DB_PATH):
    allowed={'status','stage','objective','asset_ids_json','production_job_ids_json','publishing_job_ids_json','next_action','blockers_json'}
    clean={k:v for k,v in updates.items() if k in allowed and v is not None}
    for k in ('asset_ids','production_job_ids','publishing_job_ids','blockers'):
        if k in updates: clean[k+'_json']=json.dumps(updates[k])
    if not clean:return get_campaign(campaign_id,path)
    clean['updated_at']=datetime.now(timezone.utc).isoformat()
    with _connect(path) as conn:
        if not conn.execute("SELECT 1 FROM campaigns WHERE id=?",(campaign_id,)).fetchone():return None
        sets=', '.join(f'{k}=?' for k in clean); conn.execute(f"UPDATE campaigns SET {sets} WHERE id=?",(*clean.values(),campaign_id))
    return get_campaign(campaign_id,path)
