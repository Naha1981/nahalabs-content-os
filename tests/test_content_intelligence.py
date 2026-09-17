from backend.app.content_intelligence import normalise_pattern, generate_concepts


def test_normalise_pattern_preserves_source_and_tags():
    item = normalise_pattern({"title":"Demo", "source_url":"https://example.com/x", "tags":["hook","ugc"]})
    assert item["source_url"].startswith("https://")
    assert item["tags"] == ["hook","ugc"]


def test_generate_concepts_is_original_and_pattern_aware():
    p = {"name":"Acme Hair", "category":"hair salon", "social_gap":{"state":"OBSERVED"}}
    patterns = [{"id":1,"title":"Proof reel"}]
    concepts = generate_concepts(p, patterns)
    assert len(concepts) == 3
    assert concepts[0]["source_pattern"] == "Proof reel"
    assert "original" not in concepts[0]["title"].lower() or concepts[0]["originality_note"]


def test_unverified_gap_gets_verification_note():
    p = {"name":"Acme", "category":"plumber", "social_gap":{"state":"NOT_VERIFIED"}}
    concepts = generate_concepts(p, [])
    assert all("verification_note" in c for c in concepts)
