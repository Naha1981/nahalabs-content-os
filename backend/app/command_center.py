from __future__ import annotations
from pathlib import Path
from typing import Any
from .storage import DB_PATH, _connect

STAGE_ORDER = {"PLAN":0,"CONTENT":1,"APPROVAL":2,"PRODUCTION":3,"PUBLISH":4,"MEASURE":5}

def campaign_command_center(path: Path = DB_PATH) -> dict[str, Any]:
    with _connect(path) as conn:
        rows = conn.execute("""
          SELECT c.*, p.name AS prospect_name, p.city, p.category, p.score, p.grade,
                 p.priority, p.qualification_status, p.contact_status,
                 (SELECT COUNT(*) FROM content_assets a WHERE a.prospect_id=c.prospect_id) AS content_count,
                 (SELECT COUNT(*) FROM production_jobs j WHERE j.prospect_id=c.prospect_id) AS production_count,
                 (SELECT COUNT(*) FROM publishing_jobs j WHERE j.prospect_id=c.prospect_id) AS publishing_count,
                 (SELECT COUNT(*) FROM performance_observations o WHERE o.prospect_id=c.prospect_id) AS performance_count,
                 (SELECT COUNT(*) FROM outreach_events e WHERE e.prospect_id=c.prospect_id) AS outreach_count,
                 (SELECT e.event_type FROM outreach_events e WHERE e.prospect_id=c.prospect_id ORDER BY e.occurred_at DESC LIMIT 1) AS last_outreach_event,
                 (SELECT e.channel FROM outreach_events e WHERE e.prospect_id=c.prospect_id ORDER BY e.occurred_at DESC LIMIT 1) AS last_outreach_channel,
                 (SELECT e.occurred_at FROM outreach_events e WHERE e.prospect_id=c.prospect_id ORDER BY e.occurred_at DESC LIMIT 1) AS last_outreach_at,
                 (SELECT COUNT(*) FROM revenue_events r WHERE r.prospect_id=c.prospect_id) AS revenue_event_count,
                 (SELECT COALESCE(SUM(r.amount),0) FROM revenue_events r WHERE r.prospect_id=c.prospect_id AND r.event_type IN ('WON','REVENUE')) AS commercial_value,
                 (SELECT COUNT(*) FROM revenue_events r WHERE r.prospect_id=c.prospect_id AND r.event_type='LEAD') AS revenue_leads,
                 (SELECT COUNT(*) FROM revenue_events r WHERE r.prospect_id=c.prospect_id AND r.event_type='MEETING') AS meetings,
                 (SELECT COUNT(*) FROM revenue_events r WHERE r.prospect_id=c.prospect_id AND r.event_type='WON') AS won_count
          FROM campaigns c JOIN prospects p ON p.id=c.prospect_id
          ORDER BY CASE c.status WHEN 'BLOCKED' THEN 0 WHEN 'AWAITING_APPROVAL' THEN 1 WHEN 'IN_PRODUCTION' THEN 2 WHEN 'READY_TO_PUBLISH' THEN 3 WHEN 'MEASURING' THEN 4 WHEN 'COMPLETED' THEN 5 ELSE 6 END,
                   c.updated_at DESC
        """).fetchall()
    campaigns=[]
    counts={"total":0,"active":0,"blocked":0,"awaiting_approval":0,"in_production":0,"ready_to_publish":0,"measuring":0,"completed":0}
    for row in rows:
        d=dict(row)
        import json
        for k in ("asset_ids_json","production_job_ids_json","publishing_job_ids_json","blockers_json"):
            out=k[:-5]
            d[out]=json.loads(d.pop(k) or "[]")
        d["stage_index"]=STAGE_ORDER.get(d.get("stage"),-1)
        d["has_blockers"]=bool(d.get("blockers"))
        campaigns.append(d)
        counts["total"] += 1
        status=d["status"]
        if status not in {"COMPLETED","BLOCKED"}: counts["active"] += 1
        if status=="BLOCKED": counts["blocked"] += 1
        if status=="AWAITING_APPROVAL": counts["awaiting_approval"] += 1
        if status=="IN_PRODUCTION": counts["in_production"] += 1
        if status=="READY_TO_PUBLISH": counts["ready_to_publish"] += 1
        if status=="MEASURING": counts["measuring"] += 1
        if status=="COMPLETED": counts["completed"] += 1
    return {"counts":counts,"campaigns":campaigns}
