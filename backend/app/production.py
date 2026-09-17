from __future__ import annotations
from typing import Any


def build_production_brief(asset: dict[str, Any], prospect: dict[str, Any], platform: str = "INSTAGRAM_REELS") -> dict[str, Any]:
    name = prospect.get("name", "the business")
    category = prospect.get("category", "local business")
    script = asset.get("script", "").strip()
    hook = asset.get("hook", "").strip()
    cta = asset.get("cta", "").strip()
    return {
        "production_type": "UGC_VIDEO" if asset.get("type") == "REEL_SCRIPT" else "SOCIAL_POST",
        "platform": platform,
        "aspect_ratio": "9:16" if platform in {"INSTAGRAM_REELS", "TIKTOK", "YOUTUBE_SHORTS"} else "1:1",
        "duration_seconds": 30 if asset.get("type") == "REEL_SCRIPT" else 15,
        "title": asset.get("title") or f"{name} content asset",
        "hook": hook,
        "voiceover": script,
        "cta": cta,
        "shot_list": [
            f"Establish the real {name} location, team or service.",
            f"Show the {category} service/product in action.",
            "Capture one genuine proof point: review, process, result or customer experience.",
            "Show a clear next step: booking, enquiry or visit.",
        ],
        "b_roll": ["Exterior/signage", "Team/service in action", "Close-up of relevant work/product", "Customer-facing environment"],
        "on_screen_text": [hook] if hook else [],
        "source_content_asset_id": asset.get("id"),
        "verification_state": asset.get("verification_state", "DRAFT"),
        "production_notes": "Use genuine footage and verified claims only. Obtain permission for identifiable customers/staff before publication.",
        "status": "BRIEF_READY",
    }
