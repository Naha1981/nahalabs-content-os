from __future__ import annotations
from typing import Any


def _evidence(prospect: dict[str, Any]) -> list[dict[str, Any]]:
    return [e for e in (prospect.get('evidence') or []) if e.get('state') in {'OBSERVED','VERIFIED'} and e.get('source_url')]


def generate_content_assets(prospect: dict[str, Any], patterns: list[dict[str, Any]], count: int = 3, learning: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    name = prospect.get('name') or 'the business'
    category = prospect.get('category') or 'local business'
    city = prospect.get('city') or 'your area'
    gap = prospect.get('social_gap') or {}
    verified = gap.get('state') == 'OBSERVED'
    ev = _evidence(prospect)
    proof = ev[0].get('value') if ev else ''
    contact = prospect.get('phone') or 'your usual enquiry channel'
    source = patterns[0].get('title') if patterns else 'Built-in proof-first pattern'
    learning = learning or {}
    learning_brief = learning.get('brief') or ''
    learning_note = f" Learning signal: {learning_brief}" if learning_brief else ''
    assets = [
        {
            'type':'REEL_SCRIPT','title':f'{name}: show the proof',
            'hook':f'Looking for a {category} in {city}? Start with the result, not the sales pitch.',
            'script':f'Hook: Looking for a {category} in {city}?\n\nShow: Film the real service/result at {name}.\n\nProof: {proof or "Use a genuine customer result, process or review here."}\n\nValue: Explain one thing customers should know before choosing a provider.\n\nCTA: Message {name} to ask about the service or booking.',
            'caption':f'People want to know what the experience is actually like. {name} can show the work, explain the process and make the next step simple.\n\nMessage us to enquire.',
            'cta':f'Message {name} to enquire.', 'pattern_source':source,
            'verification_state':'VERIFIED' if verified else 'DRAFT',
            'notes':'Use only genuine footage and verified claims. Do not imply a customer outcome unless evidenced.' + learning_note
        },
        {
            'type':'FAQ_POST','title':f'3 questions customers ask {name}',
            'hook':'Before you book, these are the questions worth answering.',
            'script':f'Question 1: What should a customer know before booking {name}?\nAnswer: Use the business\'s verified process or policy.\n\nQuestion 2: What does the service include?\nAnswer: State the actual current offer.\n\nQuestion 3: How do I get started?\nAnswer: {contact}.',
            'caption':f'If you are considering {name}, here are three questions worth answering before you book. Save this post and send us your next question.',
            'cta':'Send the next customer question by DM or WhatsApp.', 'pattern_source':patterns[1].get('title') if len(patterns)>1 else 'Built-in FAQ pattern',
            'verification_state':'VERIFIED' if verified else 'DRAFT',
            'notes':'Replace placeholders with facts confirmed by the business before publishing.' + learning_note
        },
        {
            'type':'REACTIVATION_POST','title':f'We are here when you need {name}',
            'hook':f'It has been quiet online. The business itself is still the story.',
            'script':f'Open: Show the storefront, team or service in action.\n\nSay: "If you have been looking for a {category} in {city}, here is what {name} does."\n\nShow: 3 current services, products or proof points that the business confirms.\n\nCTA: Make the next step clear using the verified contact or booking route.',
            'caption':f'{name} has something worth showing again: the real people, work and service behind the business.\n\nIf you are in {city} and need a {category}, get in touch.',
            'cta':f'Enquire with {name}.', 'pattern_source':patterns[2].get('title') if len(patterns)>2 else 'Built-in reactivation pattern',
            'verification_state':'VERIFIED' if verified else 'DRAFT',
            'notes':(('The quiet-period statement is only publishable when Social Gap evidence is verified.' if verified else 'Do not state that the business has gone quiet until Social Gap evidence is verified.') + learning_note)
        },
    ]
    return assets[:max(1,min(count,3))]
