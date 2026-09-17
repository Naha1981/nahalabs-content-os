from pathlib import Path
from backend.app.media_layer import synthesize_voiceover, make_captions

def test_voiceover_and_captions_are_real_files(tmp_path: Path):
    v=synthesize_voiceover('Welcome to our local business. Book today.', tmp_path)
    c=make_captions('Welcome to our local business. Book today.', tmp_path, duration=6)
    assert v['status']=='READY' and Path(v['media_path']).stat().st_size>0
    assert c['cue_count']==1 and Path(c['media_path']).read_text().count('-->')==1
