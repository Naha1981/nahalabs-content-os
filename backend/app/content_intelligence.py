from __future__ import annotations
from typing import Any


def normalise_pattern(payload: dict[str, Any]) -> dict[str, Any]:
    """Turn a saved inspiration into a searchable PatternVault record.
    Extraction/transcription can be supplied by a later worker; this layer never invents source evidence.
    """
    return {
        "title": (payload.get("title") or "Untitled pattern").strip(),
        "source_url": payload.get("source_url") or "",
        "source_type": (payload.get("source_type") or "URL").upper(),
        "transcript": payload.get("transcript") or "",
        "hook": payload.get("hook") or "",
        "promise": payload.get("promise") or "",
        "structure": payload.get("structure") or "",
        "cta": payload.get("cta") or "",
        "angle": payload.get("angle") or "",
        "audience": payload.get("audience") or "",
        "format": payload.get("format") or "",
        "emotional_trigger": payload.get("emotional_trigger") or "",
        "tags": payload.get("tags") or [],
        "notes": payload.get("notes") or "",
    }


def generate_concepts(prospect: dict[str, Any], patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate original content concepts from prospect facts + saved patterns.
    Patterns are treated as structural inspiration, not text to copy.
    """
    category = prospect.get("category") or "local business"
    name = prospect.get("name") or "the business"
    gap = prospect.get("social_gap") or {}
    concepts = [
        {
            "title": f"The {category} result customers should see",
            "format": "Short-form video",
            "hook": f"If you run a {category}, show the result before you explain the service.",
            "angle": "Proof-first local content",
            "cta": "Invite a local enquiry or booking.",
            "source_pattern": patterns[0].get("title") if patterns else "Built-in proof-first pattern",
            "originality_note": "Uses the pattern's structure only; the story, wording and proof should come from this business.",
        },
        {
            "title": f"3 questions customers ask {name}",
            "format": "FAQ/Reel",
            "hook": "Answer the questions people ask before they commit.",
            "angle": "Trust-building FAQ",
            "cta": "Ask viewers to send the next question by WhatsApp or DM.",
            "source_pattern": patterns[1].get("title") if len(patterns) > 1 else "Built-in FAQ pattern",
            "originality_note": "Questions should be sourced from this business's real customer interactions.",
        },
        {
            "title": "A reason to come back this week",
            "format": "Offer/local post",
            "hook": "Give existing followers one current reason to act now.",
            "angle": "Reactivation + local offer",
            "cta": "Use the business's verified booking/contact route.",
            "source_pattern": patterns[2].get("title") if len(patterns) > 2 else "Built-in reactivation pattern",
            "originality_note": "Offer and claims must be supplied by the business; no revenue outcome is assumed.",
        },
    ]
    if gap.get("state") != "OBSERVED":
        for c in concepts:
            c["verification_note"] = "Social Gap is not verified; treat these as general content concepts, not reactivation claims."
    return concepts
