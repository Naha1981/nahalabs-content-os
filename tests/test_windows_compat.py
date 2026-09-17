from pathlib import Path

from backend.app.media_layer import _binary
from backend.app.renderer import _escape_filter_path

def test_filter_path_escapes_windows_drive_and_separators():
    assert _escape_filter_path(r"C:\Windows\Fonts\arial.ttf") == "C\\:/Windows/Fonts/arial.ttf"

def test_eight_version_requirements_include_tzdata():
    text = Path("backend/requirements.txt").read_text(encoding="utf-8")
    assert "tzdata==2026.4" in text
