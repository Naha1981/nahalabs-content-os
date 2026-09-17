from datetime import datetime, timezone

from backend.app.social_evidence import extract_social_evidence, platform_from_url


def test_platform_detection():
    assert platform_from_url("https://www.instagram.com/acme/") == "instagram"
    assert platform_from_url("https://www.tiktok.com/@acme") == "tiktok"


def test_extracts_public_dates_and_followers_from_embedded_metadata():
    html = '''
    <html><head>
      <meta property="article:published_time" content="2026-02-01T12:00:00+00:00">
      <meta name="followers" content="2,500 followers">
      <script type="application/ld+json">
        {"datePublished":"2026-01-15T10:00:00Z"}
      </script>
    </head><body><time datetime="2025-12-20"></time></body></html>
    '''
    result = extract_social_evidence(
        html,
        "https://www.instagram.com/acme/",
        now=datetime(2026, 9, 17, tzinfo=timezone.utc),
    )
    assert result["platform"] == "instagram"
    assert result["followers"] == 2500
    assert len(result["post_dates"]) == 3
    assert result["activity"]["last_post_days"] == 227
    assert result["evidence"][0]["state"] == "OBSERVED"


def test_missing_metrics_are_not_invented():
    result = extract_social_evidence(
        "<html><body><p>Profile</p></body></html>",
        "https://www.facebook.com/acme/",
    )
    assert result["followers"] is None
    assert result["post_dates"] == []
    assert result["evidence"] == []
    assert result["activity"]["inactivity_band"] == "NOT_VERIFIED"
