from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .storage import DB_PATH, _connect

EVENTS={"LEAD","MEETING","OPPORTUNITY","WON","LOST","REVENUE"}

def init_revenue_db(path:Path=DB_PATH)->None:
    with _connect(path) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS revenue_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, prospect_id INTEGER NOT NULL,
            campaign_id INTEGER, performance_observation_id INTEGER, event_type TEXT NOT NULL,
            amount REAL NOT NULL DEFAULT 0, currency TEXT NOT NULL DEFAULT 'ZAR',
            source TEXT NOT NULL DEFAULT 'MANUAL', note TEXT NOT NULL DEFAULT '',
            occurred_at TEXT NOT NULL, created_at TEXT NOT NULL)''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_revenue_prospect ON revenue_events(prospect_id, occurred_at DESC)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_revenue_campaign ON revenue_events(campaign_id, occurred_at DESC)')

def create_revenue_event(prospect_id:int,event_type:str,amount:float=0,currency:str='ZAR',campaign_id:int|None=None,performance_observation_id:int|None=None,source:str='MANUAL',note:str='',occurred_at:str='',path:Path=DB_PATH)->dict[str,Any]:
    if event_type not in EVENTS: raise ValueError(f'Invalid event_type: {event_type}')
    now=datetime.now(timezone.utc).isoformat(); occurred_at=occurred_at or now
    with _connect(path) as conn:
        cur=conn.execute('''INSERT INTO revenue_events(prospect_id,campaign_id,performance_observation_id,event_type,amount,currency,source,note,occurred_at,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)''',(prospect_id,campaign_id,performance_observation_id,event_type,max(0,float(amount)),currency,source,note,occurred_at,now))
        eid=cur.lastrowid
    return get_revenue_event(eid,path)

def get_revenue_event(event_id:int,path:Path=DB_PATH):
    with _connect(path) as conn: row=conn.execute('SELECT * FROM revenue_events WHERE id=?',(event_id,)).fetchone()
    return dict(row) if row else None

def revenue_summary(prospect_id:int,campaign_id:int|None=None,path:Path=DB_PATH)->dict[str,Any]:
    with _connect(path) as conn:
        if campaign_id is None: rows=conn.execute('SELECT * FROM revenue_events WHERE prospect_id=? ORDER BY occurred_at DESC',(prospect_id,)).fetchall()
        else: rows=conn.execute('SELECT * FROM revenue_events WHERE prospect_id=? AND campaign_id=? ORDER BY occurred_at DESC',(prospect_id,campaign_id)).fetchall()
    events=[dict(r) for r in rows]
    counts={e:sum(1 for r in events if r['event_type']==e) for e in EVENTS}
    won=sum(r['amount'] for r in events if r['event_type']=='WON')
    revenue=sum(r['amount'] for r in events if r['event_type']=='REVENUE')
    return {'prospect_id':prospect_id,'campaign_id':campaign_id,'counts':counts,'won_value':round(won,2),'revenue':round(revenue,2),'commercial_value':round(won+revenue,2),'events':events}
