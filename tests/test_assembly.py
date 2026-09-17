from pathlib import Path
from unittest.mock import patch
from backend.app.assembly import assemble_mp4

def test_assembly_requires_clips(tmp_path: Path):
    try: assemble_mp4([], tmp_path)
    except ValueError as e: assert 'At least one clip' in str(e)
    else: assert False

def test_assembly_creates_mp4_from_real_clips(tmp_path: Path):
    import subprocess, shutil
    if not shutil.which('ffmpeg'): return
    a=tmp_path/'a.mp4'; b=tmp_path/'b.mp4'
    for p, text in [(a,'A'),(b,'B')]:
        subprocess.run(['ffmpeg','-y','-f','lavfi','-i','color=c=black:s=720x1280:r=24:d=1','-c:v','libx264','-pix_fmt','yuv420p',str(p)],capture_output=True,check=True)
    result=assemble_mp4([{'media_path':str(a)},{'media_path':str(b)}],tmp_path)
    assert result['status']=='ASSEMBLED' and result['clip_count']==2
    assert Path(result['media_path']).exists() and Path(result['media_path']).stat().st_size>1000
