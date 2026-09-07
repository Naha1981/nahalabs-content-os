from __future__ import annotations
import json, shutil, subprocess, tempfile
from pathlib import Path
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import GeneratedAsset, MediaAsset, QualityCheck
from app.services.storage import S3Storage
from app.services.quality import QualityGate

ASPECTS = {'9:16': (9,16), '1:1': (1,1), '16:9': (16,9), '4:5': (4,5)}

def _probe(path: str) -> dict[str, Any]:
    if not shutil.which('ffprobe'):
        return {}
    p = subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',path], capture_output=True, text=True, timeout=30)
    if p.returncode != 0: return {}
    return json.loads(p.stdout or '{}')

def _ratio(width: int, height: int) -> str:
    if not width or not height: return 'unknown'
    candidates = [(k, abs(width/height - a/b)) for k,(a,b) in ASPECTS.items()]
    return min(candidates, key=lambda x:x[1])[0]

async def run_quality_check(db: AsyncSession, asset: GeneratedAsset) -> QualityCheck:
    metadata = dict(asset.asset_metadata or {})
    media = await db.get(MediaAsset, asset.media_asset_id) if asset.media_asset_id else None
    probe = {}
    if media:
        with tempfile.TemporaryDirectory(prefix='quality-') as td:
            local = Path(td) / ('asset.mp4' if asset.asset_type == 'video' else 'asset.bin')
            try:
                S3Storage().download(media.storage_key, str(local))
                probe = _probe(str(local))
            except Exception as exc:
                metadata['download_error'] = str(exc)
    expected = str(metadata.get('aspect_ratio', '9:16'))
    streams = probe.get('streams', [])
    video = next((s for s in streams if s.get('codec_type') == 'video'), None)
    width = int((video or {}).get('width', 0) or 0)
    height = int((video or {}).get('height', 0) or 0)
    duration = float((probe.get('format') or {}).get('duration', 0) or 0)
    technical = 1.0
    issues=[]; warnings=[]
    if not media: issues.append('media_missing'); technical=0.0
    if media and asset.asset_type == 'video' and not probe: warnings.append('ffprobe_unavailable_or_unreadable')
    if video:
        actual = _ratio(width,height)
        if expected in ASPECTS and actual != expected:
            issues.append('aspect_ratio_mismatch'); technical=min(technical,.5)
        if duration <= 0: issues.append('invalid_duration'); technical=0.0
        if duration > 180: issues.append('duration_over_180_seconds'); technical=min(technical,.5)
    visual = float(metadata.get('visual_score', 1.0))
    brand = float(metadata.get('brand_score', 1.0))
    platform = float(metadata.get('platform_score', 1.0))
    safety = 0.0 if metadata.get('unsafe') else 1.0
    if metadata.get('unsafe'): issues.append('safety_flag')
    gate = QualityGate().evaluate(asset_type=asset.asset_type, metadata={**metadata,'output_present':bool(media),'aspect_ratio':_ratio(width,height) if video else expected,'unsafe':metadata.get('unsafe',False)}, required_aspect_ratio=expected)
    issues.extend(x for x in gate.issues if x not in issues)
    scores = [technical, visual, brand, platform, safety]
    overall = round(sum(scores)/len(scores), 4)
    passed = not issues and overall >= .8
    check = QualityCheck(generated_asset_id=asset.id,status='passed' if passed else 'needs_review',overall_score=overall,technical_score=technical,visual_score=visual,brand_score=brand,platform_score=platform,safety_score=safety,issues=issues,warnings=warnings,evidence={'width':width,'height':height,'duration_seconds':duration,'detected_aspect_ratio':_ratio(width,height),'expected_aspect_ratio':expected,'mime_type':media.mime_type if media else None})
    db.add(check)
    asset.quality_score=overall; asset.brand_score=brand; asset.platform_score=platform
    asset.status='approved_ready' if passed else 'quality_failed'
    asset.asset_metadata={**metadata,'quality_gate':{'status':check.status,'overall_score':overall,'issues':issues,'warnings':warnings}}
    return check
