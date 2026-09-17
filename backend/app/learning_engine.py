from __future__ import annotations
from typing import Any
from .performance import learning_summary


def build_content_learning(prospect_id: int, path=None) -> dict[str, Any]:
    summary = learning_summary(prospect_id, path) if path else learning_summary(prospect_id)
    obs = summary.get('observations', 0)
    if not obs:
        return {'status':'NO_SIGNAL','brief':'No observed performance yet. Use the standard evidence-first content mix.', 'signals':[]}
    signals=[]
    totals=summary['totals']
    if totals.get('engagement_rate',0) >= 5:
        signals.append(f"Prioritize formats that generate engagement; recorded aggregate engagement rate is {totals['engagement_rate']}%.")
    if totals.get('leads',0) > 0:
        signals.append(f"Keep a clear enquiry CTA; recorded content generated {totals['leads']} lead(s).")
    if summary.get('by_platform'):
        best=max(summary['by_platform'], key=lambda x:(x.get('engagement_rate',0),x.get('leads',0),x.get('views',0)))
        signals.append(f"Current platform signal: {best['platform']} has the strongest recorded engagement/lead combination.")
    top=summary.get('top_observations') or []
    if top:
        signals.append(f"Reuse the structural characteristics of top observation #{top[0]['id']} while creating an original concept.")
    return {'status':'READY','observations':obs,'signals':signals,'brief':' '.join(signals) or 'Continue collecting performance observations before changing strategy.'}
