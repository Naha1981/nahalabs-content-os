from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class MediaQualityResult:
    passed: bool
    score: float
    reasons: tuple[str, ...]

def validate_video_probe(probe: dict, expected_width: int, expected_height: int, max_duration: float = 180.0) -> MediaQualityResult:
    streams = probe.get('streams', [])
    video = next((s for s in streams if s.get('codec_type') == 'video'), None)
    if not video:
        return MediaQualityResult(False, 0.0, ('missing_video_stream',))
    width, height = int(video.get('width', 0)), int(video.get('height', 0))
    duration = float(probe.get('format', {}).get('duration', 0) or 0)
    reasons = []
    if width != expected_width or height != expected_height: reasons.append('unexpected_dimensions')
    if duration <= 0 or duration > max_duration: reasons.append('invalid_duration')
    if video.get('codec_name') not in {'h264', 'hevc', 'vp9', 'av1'}: reasons.append('unsupported_delivery_codec')
    score = max(0.0, 1.0 - 0.25 * len(reasons))
    return MediaQualityResult(not reasons, score, tuple(reasons))
