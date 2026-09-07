from __future__ import annotations
import shutil, subprocess
from pathlib import Path
from app.domain.contracts import MediaRenderer, RenderRequest

class FFmpegRenderer(MediaRenderer):
    def __init__(self, binary: str = 'ffmpeg') -> None:
        self.binary = binary
        if shutil.which(binary) is None:
            raise RuntimeError('ffmpeg is required by the media worker')

    def render(self, request: RenderRequest) -> str:
        out = Path(request.output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        vf = [
            f'scale={request.width}:{request.height}:force_original_aspect_ratio=decrease',
            f'pad={request.width}:{request.height}:(ow-iw)/2:(oh-ih)/2',
        ]
        cmd = [self.binary, '-hide_banner', '-loglevel', 'error', '-y']
        if request.start_seconds is not None:
            cmd += ['-ss', str(request.start_seconds)]
        cmd += ['-i', request.input_path]
        if request.duration_seconds is not None:
            cmd += ['-t', str(request.duration_seconds)]
        if request.audio_path:
            cmd += ['-i', request.audio_path, '-map', '0:v:0', '-map', '1:a:0', '-shortest']
        else:
            cmd += ['-map', '0:v:0', '-map', '0:a?']
        if request.burn_captions and request.caption_file:
            # ffmpeg subtitles filter is safest when the path is passed through its escaping rules.
            caption = str(Path(request.caption_file).resolve()).replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")
            vf.append(f"subtitles='{caption}'")
        cmd += ['-vf', ','.join(vf), '-r', str(request.fps), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '128k', str(out)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return str(out)

    def probe(self, path: str) -> dict:
        ffprobe = shutil.which('ffprobe')
        if not ffprobe:
            raise RuntimeError('ffprobe is required by the media worker')
        result = subprocess.run([
            ffprobe, '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', path
        ], check=True, capture_output=True, text=True)
        import json
        return json.loads(result.stdout)
