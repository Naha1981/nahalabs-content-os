from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .storage import DB_PATH, _connect

STAGES=("DISCOVERY","QUALIFIED","PROPOSAL","NEGOTIATION","WON","LOST")

def init_crm_db(path: Path=DB_PATH)->None:
    with _connect(path) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS opportunities (
          id INTEGER PRIMARY KEY AUTOINCREMENT, prospect_id INTEGER NOT NULL, campaign_id INTEGER,
          name TEXT NOT NULL, stage TEXT NOT NULL DEFAULT 'DISCOVERY', value REAL NOT NULL DEFAULT 0,
          currency TEXT NOT NULL DEFAULT 'ZAR', owner TEXT NOT NULL DEFAULT '',
          next_follow_up_at TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS opportunity_history (
          id INTEGER PRIMARY KEY AUTOINCREMENT, opportunity_id INTEGER NOT NULL, from_stage TEXT NOT NULL DEFAULT '',
          to_stage TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', occurred_at TEXT NOT NULL)''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_opportunities_prospect ON opportunities(prospect_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_opportunities_stage ON opportunities(stage)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_opp_history_opp ON opportunity_history(opportunity_id, occurred_at DESC)')

def _row(row): return dict(row) if row else None

def create_opportunity(prospect_id:int,name:str,value:float=0,currency:str='ZAR',campaign_id:int|None=None,owner:str='',next_follow_up_at:str='',note:str='',stage:str='DISCOVERY',path:Path=DB_PATH)->dict[str,Any]:
    if stage not in STAGES: raise ValueError(f'Invalid stage: {stage}')
    now=datetime.now(timezone.utc).isoformat()
    with _connect(path) as conn:
        cur=conn.execute('INSERT INTO opportunities(prospect_id,campaign_id,name,stage,value,currency,owner,next_follow_up_at,note,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(prospect_id,campaign_id,name,stage,max(0,float(value)),currency,owner,next_follow_up_at,note,now,now))
        oid=cur.lastrowid
        conn.execute('INSERT INTO opportunity_history(opportunity_id,to_stage,occurred_at) VALUES(?,?,?)',(oid,stage,now))
    return get_opportunity(oid,path)

def get_opportunity(opportunity_id:int,path:Path=DB_PATH):
    with _connect(path) as conn:
        row=conn.execute('SELECT * FROM opportunities WHERE id=?',(opportunity_id,)).fetchone()
        if not row:return None
        d=dict(row); d['history']=[dict(r) for r in conn.execute('SELECT * FROM opportunity_history WHERE opportunity_id=? ORDER BY occurred_at DESC',(opportunity_id,)).fetchall()]
    return d

def list_opportunities(prospect_id:int|None=None,path:Path=DB_PATH,limit:int=100):
    with _connect(path) as conn:
        if prospect_id is None: rows=conn.execute('SELECT * FROM opportunities ORDER BY updated_at DESC LIMIT ?',(limit,)).fetchall()
        else: rows=conn.execute('SELECT * FROM opportunities WHERE prospect_id=? ORDER BY updated_at DESC LIMIT ?',(prospect_id,limit)).fetchall()
    return [dict(r) for r in rows]

def update_opportunity(opportunity_id:int,updates:dict[str,Any],path:Path=DB_PATH):
    allowed={'name','value','currency','owner','next_follow_up_at','note','campaign_id','stage'}
    clean={k:v for k,v in updates.items() if k in allowed and v is not None}
    with _connect(path) as conn:
        old=conn.execute('SELECT * FROM opportunities WHERE id=?',(opportunity_id,)).fetchone()
        if not old:return None
        if 'stage' in clean and clean['stage'] not in STAGES: raise ValueError(f"Invalid stage: {clean['stage']}")
        now=datetime.now(timezone.utc).isoformat()
        if 'value' in clean: clean['value']=max(0,float(clean['value']))
        if clean:
            sets=', '.join(f'{k}=?' for k in clean); conn.execute(f'UPDATE opportunities SET {sets},updated_at=? WHERE id=?',(*clean.values(),now,opportunity_id))
        if 'stage' in clean and clean['stage'] != old['stage']:
            conn.execute('INSERT INTO opportunity_history(opportunity_id,from_stage,to_stage,note,occurred_at) VALUES(?,?,?,?,?)',(opportunity_id,old['stage'],clean['stage'],clean.get('note',''),now))
    return get_opportunity(opportunity_id,path)

def crm_summary(path:Path=DB_PATH)->dict[str,Any]:
    rows=list_opportunities(path=path,limit=10000)
    counts={s:0 for s in STAGES}; values={s:0.0 for s in STAGES}
    for r in rows: counts[r['stage']]=counts.get(r['stage'],0)+1; values[r['stage']]=values.get(r['stage'],0)+r['value']
    pipeline=sum(r['value'] for r in rows if r['stage'] not in ('WON','LOST'))
    won=values['WON']
    return {'counts':counts,'values':{k:round(v,2) for k,v in values.items()},'pipeline_value':round(pipeline,2),'won_value':round(won,2),'opportunities':rows}
