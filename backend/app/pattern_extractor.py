from __future__ import annotations
import re
from typing import Any


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]


def extract_pattern(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract a PatternVault record from supplied transcript/text.
    No external fetching or invented claims occur here. Missing fields are marked NOT_EXTRACTED.
    """
    text = (payload.get("transcript") or payload.get("text") or "").strip()
    sentences = _sentences(text)
    lower = text.lower()

    hook = sentences[0] if sentences else "NOT_EXTRACTED"
    cta = next((s for s in sentences if re.search(r'\b(call|book|dm|message|comment|follow|click|visit|shop|buy|learn more|sign up)\b', s, re.I)), "NOT_EXTRACTED")
    promise = next((s for s in sentences if re.search(r'\b(will|helps?|get|learn|discover|show you|how to|so you can|save|avoid|increase|improve)\b', s, re.I)), "NOT_EXTRACTED")

    if re.search(r'\b(3|three|5|five|steps|tips|ways|reasons|things)\b', lower):
        structure = "List / educational sequence"
    elif re.search(r'\b(before|after|result|transformation)\b', lower):
        structure = "Problem → proof/result → explanation"
    elif re.search(r'\b(story|when i|we started|my journey|client)\b', lower):
        structure = "Story → problem → resolution"
    else:
        structure = "Hook → explanation → CTA" if sentences else "NOT_EXTRACTED"

    fmt = "Short-form video" if re.search(r'\b(reel|tiktok|video|watch)\b', lower) else "Text/content"
    trigger = "curiosity" if re.search(r'\b(why|secret|mistake|did you know|truth)\b', lower) else "utility" if re.search(r'\b(how to|tips|steps|guide)\b', lower) else "proof" if re.search(r'\b(result|before|after|client|customer|case study)\b', lower) else "NOT_EXTRACTED"
    angle = "Educational" if structure.startswith("List") else "Proof-led" if "proof" in structure else "Story-led" if "Story" in structure else "Direct value"

    return {
        "title": (payload.get("title") or (hook[:80] if hook != "NOT_EXTRACTED" else "Untitled pattern")).strip(),
        "source_url": payload.get("source_url") or "",
        "source_type": (payload.get("source_type") or "TRANSCRIPT").upper(),
        "transcript": text,
        "hook": hook,
        "promise": promise,
        "structure": structure,
        "cta": cta,
        "angle": angle,
        "audience": payload.get("audience") or "NOT_EXTRACTED",
        "format": fmt,
        "emotional_trigger": trigger,
        "tags": payload.get("tags") or [],
        "notes": payload.get("notes") or "Extracted from supplied text; verify against the source before publishing.",
        "extraction_status": "EXTRACTED" if text else "NEEDS_TRANSCRIPT",
        "evidence_state": "OBSERVED" if text else "NOT_VERIFIED",
    }
