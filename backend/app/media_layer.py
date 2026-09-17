from __future__ import annotations
import re, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

class MediaLayerUnavailable(RuntimeError):
    pass

def _binary(name: str) -> str:
    p = shutil.which(name)
    if p:
        return p
    # Windows installers may add binaries to PATH only for future shells.
    if name.lower() == 'espeak':
        candidates = [
            Path(r"C:\Program Files\eSpeak\command_line\espeak.exe"),
            Path(r"C:\Program Files (x86)\eSpeak\command_line\espeak.exe"),
            Path('/usr/bin/espeak'),
            Path('/usr/local/bin/espeak'),
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
    raise MediaLayerUnavailable(f"{name} is not installed or not on PATH")

def _stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')

def synthesize_voiceover(text: str, output_dir: Path, voice: str = 'en') -> dict[str, Any]:
    """Create a real local WAV using eSpeak; no network/API required."""
    text = re.sub(r'\s+', ' ', (text or '').strip())
    if not text: raise ValueError('Voiceover text is empty')
    espeak = _binary('espeak')
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f'voice-{_stamp()}.wav'
    cmd=[espeak, '-v', voice, '-s', '155', '-w', str(out), text]
    r=subprocess.run(cmd,capture_output=True,text=True,check=False,timeout=60)
    if r.returncode or not out.exists() or out.stat().st_size == 0:
        raise RuntimeError('Voice synthesis failed: ' + ((r.stderr or '').strip()[-500:] or 'unknown error'))
    return {'provider':'LOCAL_ESPEAK','status':'READY','media_path':str(out),'media_filename':out.name,'mime_type':'audio/wav','bytes':out.stat().st_size,'voice':voice}

def _ts(seconds: float) -> str:
    ms=round(seconds*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'

def make_captions(text: str, output_dir: Path, duration: float | None = None, words_per_caption: int = 7) -> dict[str, Any]:
    words=(text or '').split()
    if not words: raise ValueError('Caption text is empty')
    output_dir.mkdir(parents=True, exist_ok=True)
    if duration is None: duration=max(3.0, len(words)/2.5)
    chunks=[words[i:i+words_per_caption] for i in range(0,len(words),words_per_caption)]
    cue=duration/len(chunks)
    out=output_dir/f'captions-{_stamp()}.srt'
    lines=[]
    for i,chunk in enumerate(chunks):
        start=i*cue; end=duration if i==len(chunks)-1 else (i+1)*cue
        lines += [str(i+1), f'{_ts(start)} --> {_ts(end)}', ' '.join(chunk), '']
    out.write_text('\n'.join(lines),encoding='utf-8')
    return {'provider':'LOCAL_CAPTION_ENGINE','status':'READY','media_path':str(out),'media_filename':out.name,'mime_type':'application/x-subrip','bytes':out.stat().st_size,'cue_count':len(chunks)}

def mux_voice_and_captions(video_path: Path, audio_path: Path, srt_path: Path, output_dir: Path) -> dict[str, Any]:
    ffmpeg=_binary('ffmpeg'); output_dir.mkdir(parents=True,exist_ok=True)
    out=output_dir/f'final-{_stamp()}.mp4'
    # SRT is burned into the video; audio replaces silent preview audio.
    srt_filter=str(srt_path.resolve()).replace('\\','/').replace(':','\\:').replace("'","\\'")
    cmd=[ffmpeg,'-y','-i',str(video_path),'-i',str(audio_path),'-vf',f"subtitles='{srt_filter}'",'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','27','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',str(out)]
    r=subprocess.run(cmd,capture_output=True,text=True,check=False,timeout=300)
    if r.returncode or not out.exists() or out.stat().st_size==0:
        err=(r.stderr or '').strip().splitlines(); raise RuntimeError('Media mux failed'+(f': {err[-1][:500]}' if err else ''))
    return {'provider':'LOCAL_FFMPEG_MEDIA_LAYER','status':'READY_TO_PUBLISH','media_path':str(out),'media_filename':out.name,'mime_type':'video/mp4','bytes':out.stat().st_size}
