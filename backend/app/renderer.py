from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RendererUnavailable(RuntimeError):
    pass


def _ffmpeg_binary() -> str:
    binary = shutil.which("ffmpeg")
    if not binary:
        raise RendererUnavailable("FFmpeg is not installed or not on PATH")
    return binary


def _font_file() -> str:
    # Prefer a Windows system font so FFmpeg does not depend on Fontconfig.
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        Path('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise RendererUnavailable("No usable Windows font was found under C:\\Windows\\Fonts")


def _escape_filter_path(path: str) -> str:
    return path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def _write_text(path: Path, text: str) -> None:
    path.write_text((text or "").strip() or " ", encoding="utf-8")


def render_local_preview(job: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Render a deterministic social-video preview with local FFmpeg.

    This is deliberately a preview renderer, not an AI video generator. It turns
    a verified production brief into a real MP4 so the rest of the pipeline can
    be exercised today. Provider-specific AI renderers can replace this adapter.
    """
    ffmpeg = _ffmpeg_binary()
    output_dir.mkdir(parents=True, exist_ok=True)
    job_id = int(job["id"])
    now = datetime.now(timezone.utc)
    stem = f"job-{job_id}-{now.strftime('%Y%m%d%H%M%S')}"
    hook_file = output_dir / f"{stem}-hook.txt"
    body_file = output_dir / f"{stem}-body.txt"
    cta_file = output_dir / f"{stem}-cta.txt"
    output_file = output_dir / f"{stem}.mp4"

    hook = job.get("hook") or job.get("title") or "NahaLabs Reactivate Preview"
    body = job.get("voiceover") or "Production brief preview: add genuine footage, proof and service details here."
    cta = job.get("cta") or "BOOK · ENQUIRE · VISIT"
    duration = max(5, min(int(job.get("duration_seconds") or 15), 60))
    first = max(2, min(4, duration // 5))
    last = max(2, min(5, duration // 5))
    middle_end = max(first + 1, duration - last)

    _write_text(hook_file, hook)
    _write_text(body_file, body)
    _write_text(cta_file, cta)

    font_file = _escape_filter_path(_font_file())

    filters = (
        f"drawtext=fontfile='{font_file}':fontcolor=white:fontsize=56:box=1:boxcolor=black@0.45:boxborderw=28:" \
        f"textfile='{hook_file.name}':x=(w-text_w)/2:y=180:enable='between(t,0,{first})',"
        f"drawtext=fontfile='{font_file}':fontcolor=white:fontsize=38:box=1:boxcolor=black@0.50:boxborderw=24:" \
        f"textfile='{body_file.name}':x=50:y=(h-text_h)/2:enable='between(t,{first},{middle_end})',"
        f"drawtext=fontfile='{font_file}':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.55:boxborderw=24:" \
        f"textfile='{cta_file.name}':x=(w-text_w)/2:y=h-240:enable='between(t,{middle_end},{duration})',"
        f"drawtext=fontfile='{font_file}':fontcolor=white@0.75:fontsize=18:text='PREVIEW - LOCAL RENDER - NOT AI GENERATED':x=20:y=20"
    )

    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"color=c=0x111827:s=720x1280:r=24:d={duration}",
        "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
        "-vf", filters,
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "29",
        "-c:a", "aac", "-b:a", "96k", "-shortest",
        "-movflags", "+faststart", str(output_file),
    ]

    try:
        completed = subprocess.run(
            cmd,
            cwd=output_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
    finally:
        for p in (hook_file, body_file, cta_file):
            p.unlink(missing_ok=True)

    if completed.returncode != 0 or not output_file.exists() or output_file.stat().st_size == 0:
        stderr = (completed.stderr or "").strip().splitlines()
        detail = "FFmpeg render failed"
        if stderr:
            detail += f": {stderr[-1][:500]}"
        raise RuntimeError(detail)

    return {
        "provider": "LOCAL_FFMPEG_PREVIEW",
        "status": "RENDERED",
        "media_path": str(output_file),
        "media_filename": output_file.name,
        "duration_seconds": duration,
        "mime_type": "video/mp4",
        "bytes": output_file.stat().st_size,
        "note": "Deterministic local preview. NOT AI GENERATED. Replace this provider with a video/UGC model for production generation.",
    }
