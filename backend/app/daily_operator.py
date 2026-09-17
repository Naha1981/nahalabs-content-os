from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .storage import DB_PATH, _connect

PRIORITY = {'HOT': 0, 'HIGH': 1, 'NORMAL': 2, 'LOW': 3}

def _due(value: str, now: datetime) -> bool:
    if not value: return False
    try:
        dt = datetime.fromisoformat(value.replace('Z','+00:00'))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt <= now
    except ValueError:
        return False

def daily_operator(path: Path = DB_PATH, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    today = now.date().isoformat()
    with _connect(path) as conn:
        prospects = conn.execute('SELECT * FROM prospects WHERE qualification_status != "DISQUALIFIED"').fetchall()
        campaigns = conn.execute('SELECT * FROM campaigns WHERE status NOT IN ("COMPLETED")').fetchall()
        opps = conn.execute('SELECT * FROM opportunities WHERE stage NOT IN ("WON","LOST")').fetchall()
        events = conn.execute('SELECT * FROM outreach_events ORDER BY occurred_at DESC').fetchall()
        pubs = conn.execute('SELECT * FROM publishing_jobs WHERE status IN ("SCHEDULED","QUEUED")').fetchall()
    last_outreach = {}
    for e in events:
        last_outreach.setdefault(e['prospect_id'], e)
    items=[]
    def add(kind, priority, prospect, action, reason, due_at='', entity_id=None):
        items.append({'kind':kind,'priority':priority,'prospect_id':prospect['id'],'prospect_name':prospect['name'],
                      'city':prospect['city'],'score':prospect['score'],'seller_priority':prospect['priority'],
                      'action':action,'reason':reason,'due_at':due_at,'entity_id':entity_id})
    by_id={p['id']:p for p in prospects}
    for p in prospects:
        if p['priority'] in ('HOT','HIGH') and p['qualification_status']=='QUALIFIED' and p['contact_status'] in ('NOT_CONTACTED','QUEUED'):
            add('OUTREACH',0 if p['priority']=='HOT' else 1,p,'Send first outreach',f'{p["priority"]} qualified prospect has no completed outreach.')
        if _due(p['follow_up_at'], now):
            add('FOLLOW_UP',0 if p['priority']=='HOT' else 1,p,'Follow up with prospect',f'Follow-up is due ({p["follow_up_at"]}).',p['follow_up_at'])
        if p['qualification_status']=='QUALIFIED' and not p['next_action']:
            add('QUALIFICATION',2,p,'Set next action', 'Qualified prospect has no recorded next action.')
    for c in campaigns:
        p=by_id.get(c['prospect_id'])
        if not p: continue
        if c['status']=='BLOCKED': add('CAMPAIGN',0,p,'Resolve campaign blocker','Campaign is blocked.',entity_id=c['id'])
        elif c['status']=='AWAITING_APPROVAL': add('APPROVAL',0,p,'Review campaign content','Human approval is required before production.',entity_id=c['id'])
        elif c['status']=='READY_TO_PUBLISH': add('PUBLISH',1,p,'Publish campaign','Campaign is ready for publishing.',entity_id=c['id'])
        elif c['status']=='MEASURING': add('MEASURE',2,p,'Record campaign performance','Campaign is awaiting observed performance data.',entity_id=c['id'])
    for o in opps:
        p=by_id.get(o['prospect_id'])
        if p and _due(o['next_follow_up_at'], now): add('DEAL_FOLLOW_UP',0 if p['priority']=='HOT' else 1,p,'Follow up on opportunity',f'Opportunity follow-up is due ({o["next_follow_up_at"]}).',o['next_follow_up_at'],o['id'])
    for j in pubs:
        p=by_id.get(j['prospect_id'])
        if p: add('PUBLISH_QUEUE',1,p,'Process publishing queue',f'{j["platform"]} publishing job is {j["status"]}.',j['scheduled_for'],j['id'])
    # Deduplicate exact prospect/action/entity combinations.
    seen=set(); unique=[]
    for x in items:
        k=(x['kind'],x['prospect_id'],x['action'],x['entity_id'])
        if k not in seen: seen.add(k); unique.append(x)
    unique.sort(key=lambda x:(x['priority'], x['due_at'] or '9999', -float(x['score'] or 0)))
    counts={}
    for x in unique: counts[x['kind']]=counts.get(x['kind'],0)+1
    return {'generated_at':now.isoformat(),'date':today,'counts':counts,'total_actions':len(unique),'actions':unique[:200]}
