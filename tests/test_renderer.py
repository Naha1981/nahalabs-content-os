from pathlib import Path

from backend.app.renderer import render_local_preview


def test_local_ffmpeg_preview_creates_real_mp4(tmp_path: Path):
    result = render_local_preview(
        {
            "id": 101,
            "title": "Salon proof",
            "hook": "Still relying on word of mouth?",
            "voiceover": "Show the work, the proof and the next step.",
            "cta": "WhatsApp us to book",
            "duration_seconds": 6,
        },
        tmp_path,
    )
    output = Path(result["media_path"])
    assert result["provider"] == "LOCAL_FFMPEG_PREVIEW"
    assert result["status"] == "RENDERED"
    assert output.exists()
    assert output.suffix == ".mp4"
    assert output.stat().st_size > 1000


def test_preview_renderer_declares_honest_boundary(tmp_path: Path):
    result = render_local_preview({"id": 102, "duration_seconds": 5}, tmp_path)
    assert "NOT AI GENERATED" in result["note"]
