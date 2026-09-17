from __future__ import annotations
from pathlib import Path
from typing import Any
from .storage import DB_PATH, _connect
from .campaigns import list_campaigns
from .outreach_events import outreach_summary
from .revenue import revenue_summary
from .crm import list_opportunities


def prospect_workspace(prospect_id: int, path: Path = DB_PATH) -> dict[str, Any] | None:
    with _connect(path) as conn:
        p = conn.execute('SELECT * FROM prospects WHERE id=?', (prospect_id,)).fetchone()
        if not p:
            return None
        prospect = dict(p)
        content = [dict(r) for r in conn.execute('SELECT * FROM content_assets WHERE prospect_id=? ORDER BY updated_at DESC LIMIT 50', (prospect_id,)).fetchall()]
        production = [dict(r) for r in conn.execute('SELECT * FROM production_jobs WHERE prospect_id=? ORDER BY updated_at DESC LIMIT 50', (prospect_id,)).fetchall()]
        publishing = [dict(r) for r in conn.execute('SELECT * FROM publishing_jobs WHERE prospect_id=? ORDER BY updated_at DESC LIMIT 50', (prospect_id,)).fetchall()]
        performance = [dict(r) for r in conn.execute('SELECT * FROM performance_observations WHERE prospect_id=? ORDER BY observed_at DESC LIMIT 50', (prospect_id,)).fetchall()]
    campaigns = list_campaigns(prospect_id, path=path, limit=50)
    outreach = outreach_summary(prospect_id, path=path)
    revenue = revenue_summary(prospect_id, path=path)
    opportunities = list_opportunities(prospect_id, path=path, limit=50)
    return {
        'prospect': prospect,
        'qualification': {
            'status': prospect.get('qualification_status'), 'priority': prospect.get('priority'),
            'contact_status': prospect.get('contact_status'), 'next_action': prospect.get('next_action'),
            'notes': prospect.get('notes'),
        },
        'evidence': {
            'website': prospect.get('website'), 'google_maps_url': prospect.get('google_maps_url'),
            'social_links': prospect.get('social_links_json') or prospect.get('social_links'),
            'evidence_state': prospect.get('evidence_state'), 'evidence': prospect.get('evidence_json') or prospect.get('evidence'),
        },
        'outreach': outreach,
        'campaigns': campaigns,
        'content_assets': content,
        'production_jobs': production,
        'publishing_jobs': publishing,
        'performance': performance,
        'revenue': revenue,
        'opportunities': opportunities,
        'summary': {
            'content': len(content), 'production': len(production), 'publishing': len(publishing),
            'performance': len(performance), 'campaigns': len(campaigns), 'outreach': outreach['count'],
            'opportunities': len(opportunities), 'pipeline_value': round(sum(o['value'] for o in opportunities if o['stage'] not in ('WON','LOST')), 2),
            'won_value': round(sum(o['value'] for o in opportunities if o['stage']=='WON'), 2),
            'revenue_value': revenue.get('total_value', revenue.get('commercial_value', 0)),
        },
    }
