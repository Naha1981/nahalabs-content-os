from datetime import datetime, timezone

import backend.app.social_pipeline as sp


def test_enrich_social_profiles_normalises_activity(monkeypatch):
    monkeypatch.setattr(
        sp,
        "collect_social_urls",
        lambda urls, **kwargs: {
            "instagram": {
                "status": "OBSERVED",
                "final_url": "https://www.instagram.com/acme/",
                "followers": 2500,
                "post_dates": [
                    "2026-02-01T12:00:00+00:00",
                    "2026-01-01T12:00:00+00:00",
                    "2025-12-01T12:00:00+00:00",
                ],
                "evidence": [{"claim": "public_post_date", "value": "2026-02-01"}],
            }
        },
    )
    result = sp.enrich_social_profiles(
        {"instagram": "https://www.instagram.com/acme/"},
        now=datetime(2026, 9, 17, tzinfo=timezone.utc),
    )
    channel = result["channels"][0]
    assert channel["followers"] == 2500
    assert channel["posts_last_365d"] == 3
    assert channel["last_meaningful_post_days"] == 227
    assert channel["inactivity_band"] == "180_364_DAYS"
    assert result["historical_activity_score"] == 25.0
    assert result["social_gap_score"] == 90.0


def test_no_public_evidence_remains_unverified(monkeypatch):
    monkeypatch.setattr(
        sp,
        "collect_social_urls",
        lambda urls, **kwargs: {
            "facebook": {
                "status": "NOT_VERIFIED",
                "final_url": "https://www.facebook.com/acme/",
                "followers": None,
                "post_dates": [],
                "evidence": [],
                "error": "blocked",
            }
        },
    )
    result = sp.enrich_social_profiles({"facebook": "https://www.facebook.com/acme/"})
    assert result["evidence_state"] == "NOT_VERIFIED"
    assert result["social_gap_score"] == 0.0
    assert result["channels"][0]["status"] == "NOT_VERIFIED"
