from __future__ import annotations
import shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class AssemblyUnavailable(RuntimeError):
    pass

def _ffmpeg() -> str:
    b = shutil.which('ffmpeg')
    if not b: raise AssemblyUnavailable('FFmpeg is not installed or not on PATH')
    return b

def assemble_mp4(clips: list[dict[str, Any]], output_dir: Path, width: int = 720, height: int = 1280) -> dict[str, Any]:
    if not clips: raise ValueError('At least one clip is required')
    ffmpeg = _ffmpeg(); output_dir.mkdir(parents=True, exist_ok=True)
    valid=[]
    for c in clips:
        p=Path(str(c.get('media_path','')))
        if not p.exists() or p.stat().st_size == 0: raise FileNotFoundError(f"Media file not found: {p}")
        valid.append(p)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    output=output_dir/f'assembly-{stamp}.mp4'
    listfile=output_dir/f'assembly-{stamp}.txt'
    # Normalize every clip to the same vertical canvas, frame rate and pixel format.
    lines=[]
    for p in valid:
        safe=str(p.resolve()).replace("'", "'\\''")
        lines.append(f"file '{safe}'")
    listfile.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    cmd=[ffmpeg,'-y','-f','concat','-safe','0','-i',str(listfile),'-vf',f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps=24,format=yuv420p",'-c:v','libx264','-preset','veryfast','-crf','28','-an','-movflags','+faststart',str(output)]
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,check=False,timeout=300)
    finally: listfile.unlink(missing_ok=True)
    if r.returncode or not output.exists() or output.stat().st_size == 0:
        err=(r.stderr or '').strip().splitlines(); raise RuntimeError('Assembly failed'+(f": {err[-1][:500]}" if err else ''))
    return {'provider':'LOCAL_FFMPEG_ASSEMBLER','status':'ASSEMBLED','media_path':str(output),'media_filename':output.name,'mime_type':'video/mp4','bytes':output.stat().st_size,'clip_count':len(valid)}
