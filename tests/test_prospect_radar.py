from backend.app.prospect_radar import radar_record


def test_radar_record_explains_social_gap_and_keeps_clickable_evidence():
    record = radar_record({
        "name": "Demo Local Business",
        "city": "Johannesburg",
        "website": "https://example.com",
        "google_url": "https://www.google.com/maps",
        "category": "Service Business",
        "health_score": 92,
        "content_dependency_score": 88,
        "monetization_score": 82,
        "reputation_score": 90,
        "historical_activity_score": 86,
        "audience_score": 72,
        "competitive_gap_score": 84,
        "contactability_score": 95,
        "social_channels": [{
            "platform": "Instagram",
            "url": "https://instagram.com/example",
            "followers": 2500,
            "posts_last_90d": 0,
            "posts_last_365d": 7,
            "last_meaningful_post_days": 190,
        }],
        "evidence": [{
            "claim": "Business website exists",
            "value": "Public website found",
            "source_url": "https://example.com",
            "state": "VERIFIED",
        }],
    })
    assert record["social_gap_score"] == 90.0
    assert record["social_gap"]["state"] == "OBSERVED"
    assert "190 days" in record["social_gap"]["details"]
    assert record["evidence"][0]["source_url"] == "https://example.com/"


def test_radar_record_without_activity_does_not_claim_a_gap():
    from backend.app.prospect_radar import radar_record
    record = radar_record({
        "name": "Unverified Social Business", "city": "Johannesburg",
        "website": "https://example.com", "category": "Service Business",
        "health_score": 80, "content_dependency_score": 80, "monetization_score": 80,
        "reputation_score": 80, "historical_activity_score": 0, "audience_score": 50,
        "competitive_gap_score": 50, "contactability_score": 80,
        "social_channels": [{"platform":"Instagram","url":"https://instagram.com/example"}],
        "evidence": []
    })
    assert record["social_gap_score"] == 0.0
    assert record["social_gap"]["state"] == "NOT_VERIFIED"
