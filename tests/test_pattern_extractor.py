from backend.app.pattern_extractor import extract_pattern


def test_extracts_observable_pattern_fields_from_transcript():
    r = extract_pattern({"title":"Demo", "source_url":"https://example.com", "transcript":"3 mistakes every salon owner should avoid. Here is how to fix them. Book a consultation today."})
    assert r["extraction_status"] == "EXTRACTED"
    assert r["evidence_state"] == "OBSERVED"
    assert r["hook"].startswith("3 mistakes")
    assert r["structure"] == "List / educational sequence"
    assert "Book" in r["cta"]


def test_missing_transcript_does_not_invent_pattern():
    r = extract_pattern({"title":"No source"})
    assert r["extraction_status"] == "NEEDS_TRANSCRIPT"
    assert r["hook"] == "NOT_EXTRACTED"
    assert r["evidence_state"] == "NOT_VERIFIED"
