from app.workers.media_worker import ASPECTS, build_srt

def test_aspect_profiles():
    assert ASPECTS['9:16'] == (1080, 1920)
    assert ASPECTS['1:1'] == (1080, 1080)

def test_build_srt(tmp_path):
    p = build_srt([{'start': 0, 'end': 1.25, 'text': 'Hello restaurant!'}], str(tmp_path/'x.srt'))
    text = (tmp_path/'x.srt').read_text()
    assert '00:00:00,000 --> 00:00:01,250' in text
    assert 'Hello restaurant!' in text
