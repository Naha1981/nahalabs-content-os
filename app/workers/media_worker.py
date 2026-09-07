from __future__ import annotations
import argparse, asyncio, json, logging, tempfile
from pathlib import Path
from uuid import UUID
from app.core.config import get_settings
from app.rendering.ffmpeg import FFmpegRenderer
from app.services.storage import S3Storage

log = logging.getLogger('nahalabs.media_worker')
logging.basicConfig(level=get_settings().log_level)

ASPECTS = {
    '9:16': (1080, 1920),
    '1:1': (1080, 1080),
    '16:9': (1920, 1080),
    '4:5': (1080, 1350),
}

def build_srt(segments: list[dict], path: str) -> str:
    def ts(seconds: float) -> str:
        ms = int(round(seconds * 1000)); h, ms = divmod(ms, 3_600_000); m, ms = divmod(ms, 60_000); s, ms = divmod(ms, 1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'
    lines = []
    for i, seg in enumerate(segments, 1):
        text = str(seg.get('text', '')).strip()
        if not text: continue
        lines += [str(i), f"{ts(float(seg['start']))} --> {ts(float(seg['end']))}", text, '']
    Path(path).write_text('\n'.join(lines), encoding='utf-8')
    return path

async def process_local(*, input_path: str, output_path: str, aspect_ratio: str = '9:16', fps: int = 30,
                        start: float | None = None, duration: float | None = None,
                        transcript_segments: list[dict] | None = None, burn_captions: bool = False) -> dict:
    if aspect_ratio not in ASPECTS: raise ValueError(f'Unsupported aspect ratio: {aspect_ratio}')
    renderer = FFmpegRenderer()
    caption_file = None
    with tempfile.TemporaryDirectory(prefix='nahalabs-render-') as td:
        if burn_captions and transcript_segments:
            caption_file = build_srt(transcript_segments, str(Path(td) / 'captions.srt'))
        from app.domain.contracts import RenderRequest
        w, h = ASPECTS[aspect_ratio]
        renderer.render(RenderRequest(input_path=input_path, output_path=output_path, width=w, height=h, fps=fps,
                                       start_seconds=start, duration_seconds=duration, burn_captions=burn_captions,
                                       caption_file=caption_file))
        probe = renderer.probe(output_path)
    return {'output_path': output_path, 'aspect_ratio': aspect_ratio, 'width': w, 'height': h, 'probe': probe}

def main() -> None:
    p = argparse.ArgumentParser(description='NahaLabs media rendering worker')
    p.add_argument('--input', required=True); p.add_argument('--output', required=True)
    p.add_argument('--aspect-ratio', default='9:16', choices=sorted(ASPECTS))
    p.add_argument('--fps', type=int, default=30); p.add_argument('--start', type=float); p.add_argument('--duration', type=float)
    p.add_argument('--captions-json'); p.add_argument('--burn-captions', action='store_true')
    args = p.parse_args()
    segments = json.loads(Path(args.captions_json).read_text()) if args.captions_json else None
    result = asyncio.run(process_local(input_path=args.input, output_path=args.output, aspect_ratio=args.aspect_ratio,
                                        fps=args.fps, start=args.start, duration=args.duration,
                                        transcript_segments=segments, burn_captions=args.burn_captions))
    print(json.dumps(result, default=str))

if __name__ == '__main__': main()
