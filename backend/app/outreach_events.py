from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .storage import DB_PATH, _connect

def init_outreach_events_db(path: Path = DB_PATH) -> None:
    with _connect(path) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS outreach_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, prospect_id INTEGER NOT NULL,
            campaign_id INTEGER, channel TEXT NOT NULL, event_type TEXT NOT NULL,
            subject TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '',
            occurred_at TEXT NOT NULL, created_at TEXT NOT NULL
        )''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_outreach_events_prospect ON outreach_events(prospect_id, occurred_at DESC)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_outreach_events_campaign ON outreach_events(campaign_id, occurred_at DESC)')

def create_outreach_event(prospect_id: int, channel: str, event_type: str, subject: str = '', note: str = '', campaign_id: int | None = None, occurred_at: str = '', path: Path = DB_PATH) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    occurred_at = occurred_at or now
    with _connect(path) as conn:
        cur = conn.execute('INSERT INTO outreach_events(prospect_id,campaign_id,channel,event_type,subject,note,occurred_at,created_at) VALUES(?,?,?,?,?,?,?,?)', (prospect_id,campaign_id,channel,event_type,subject,note,occurred_at,now))
        eid = cur.lastrowid
    return get_outreach_event(eid, path)

def get_outreach_event(event_id: int, path: Path = DB_PATH):
    with _connect(path) as conn:
        row = conn.execute('SELECT * FROM outreach_events WHERE id=?', (event_id,)).fetchone()
    return dict(row) if row else None

def list_outreach_events(prospect_id: int, campaign_id: int | None = None, limit: int = 50, path: Path = DB_PATH):
    with _connect(path) as conn:
        if campaign_id is None:
            rows = conn.execute('SELECT * FROM outreach_events WHERE prospect_id=? ORDER BY occurred_at DESC LIMIT ?', (prospect_id, limit)).fetchall()
        else:
            rows = conn.execute('SELECT * FROM outreach_events WHERE prospect_id=? AND campaign_id=? ORDER BY occurred_at DESC LIMIT ?', (prospect_id, campaign_id, limit)).fetchall()
    return [dict(r) for r in rows]

def outreach_summary(prospect_id: int, campaign_id: int | None = None, path: Path = DB_PATH):
    events = list_outreach_events(prospect_id, campaign_id, 100, path)
    return {
        'count': len(events),
        'last_event': events[0] if events else None,
        'channels': sorted({e['channel'] for e in events}),
        'event_types': sorted({e['event_type'] for e in events}),
        'events': events,
    }
