from backend.app.pattern_extractor import extract_pattern
from backend.app.source_ingestion import fetch_url_text


def test_extract_pattern_from_supplied_transcript():
    p = extract_pattern({"title":"Test", "transcript":"Stop making this mistake. We show you how to improve bookings. DM us to learn more."})
    assert p["extraction_status"] == "EXTRACTED"
    assert p["hook"] != "NOT_EXTRACTED"
    assert p["cta"] != "NOT_EXTRACTED"


def test_fetch_rejects_non_http_url():
    try:
        fetch_url_text("file:///tmp/test")
    except ValueError as exc:
        assert "http" in str(exc)
    else:
        raise AssertionError("Expected URL validation failure")
