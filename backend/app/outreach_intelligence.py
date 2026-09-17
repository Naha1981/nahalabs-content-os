from __future__ import annotations
from typing import Any


def _verified_evidence(p: dict[str, Any]) -> list[dict[str, Any]]:
    return [e for e in (p.get('evidence') or []) if e.get('source_url') and e.get('state') in {'OBSERVED','VERIFIED'}]


def build_outreach_intelligence(p: dict[str, Any]) -> dict[str, Any]:
    gap = p.get('social_gap') or {}
    evidence = _verified_evidence(p)
    signals = gap.get('signals') or []
    channels = p.get('channels') or []
    active_channels = [c for c in channels if c.get('url')]

    observed = []
    for e in evidence[:6]:
        observed.append({'claim': e.get('claim',''), 'value': e.get('value',''), 'source_url': e.get('source_url'), 'state': e.get('state')})
    for s in signals:
        observed.append({'claim': s.get('label',''), 'value': str(s.get('value','')), 'source_url': next((c.get('url') for c in channels if c.get('platform') == gap.get('signals',[{}])[0].get('value')), None), 'state': 'OBSERVED'})

    if gap.get('state') == 'OBSERVED':
        why = gap.get('details') or gap.get('headline') or 'A public Social Gap signal was observed.'
    else:
        why = 'The available public evidence does not yet verify a Social Gap. Outreach should not present inactivity as a fact.'

    opportunities = []
    category = (p.get('category') or 'local business').strip()
    if gap.get('state') == 'OBSERVED':
        opportunities.extend([
            f"Reactivation post for {category}: acknowledge the quiet period indirectly and give customers a current reason to enquire.",
            'Short-form customer-proof content using a recent service/result, with a clear local enquiry CTA.',
            'A simple weekly offer/FAQ series built around the questions customers already ask before booking or buying.'
        ])
    else:
        opportunities.append('First verify recent social activity and business status before proposing a reactivation campaign.')

    if p.get('phone'):
        cta = f"Ask customers to enquire via the existing contact route ({p['phone']})."
    elif p.get('website'):
        cta = 'Drive the next post to the existing website/contact route.'
    else:
        cta = 'Use the verified public contact route once confirmed.'

    script = (
        f"Hook: Your {category} already has a public digital footprint.\n"
        f"Proof: {why}\n"
        f"Promise: We can turn the existing audience and proven content activity into a consistent, evidence-led content engine.\n"
        f"CTA: {cta}"
    )
    message = (
        f"Hi {p.get('name','there')}, I was looking at your online presence and noticed {why[0].lower() + why[1:] if why else 'a potential content gap'}. "
        f"I work with NahaLabs on practical content systems for local businesses. I can send you a short, evidence-backed Social Gap audit showing what I found and a few content opportunities."
    )
    return {
        'state': gap.get('state','NOT_VERIFIED'),
        'what_we_observed': observed,
        'why_it_matters': why,
        'recommended_action': 'Use the evidence as the opening for a human-reviewed outreach conversation; do not promise revenue outcomes.',
        'content_opportunities': opportunities,
        'ugc_script': script,
        'outreach_message': message,
        'evidence_count': len(evidence),
    }
