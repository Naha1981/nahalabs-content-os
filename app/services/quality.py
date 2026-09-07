from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class QualityResult:
    passed: bool
    technical_score: float
    visual_score: float
    brand_score: float
    platform_score: float
    issues: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

class QualityGate:
    """Deterministic first-pass gate. Provider/model-specific CV checks can plug in later."""
    def evaluate(self, *, asset_type: str, metadata: dict[str, Any], required_aspect_ratio: str = "9:16") -> QualityResult:
        issues: list[str] = []
        technical = 1.0
        visual = float(metadata.get("visual_score", 1.0))
        brand = float(metadata.get("brand_score", 1.0))
        platform = float(metadata.get("platform_score", 1.0))
        if not metadata.get("output_present", True):
            issues.append("output_missing"); technical = 0.0
        if metadata.get("corrupt"):
            issues.append("media_corrupt"); technical = 0.0
        if metadata.get("aspect_ratio") and metadata["aspect_ratio"] != required_aspect_ratio:
            issues.append("aspect_ratio_mismatch"); platform = min(platform, 0.5)
        if metadata.get("unsafe"):
            issues.append("safety_flag"); brand = 0.0
        passed = not issues and min(technical, visual, brand, platform) >= 0.8
        return QualityResult(passed, technical, visual, brand, platform, tuple(issues), metadata)
