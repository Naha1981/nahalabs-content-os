from datetime import datetime, timezone

from backend.app.activity import (
    ActivityObservation,
    analyse_channel,
    historical_activity_score,
    inactivity_band,
    social_gap_from_activity,
)

NOW = datetime(2026, 9, 17, tzinfo=timezone.utc)


def test_activity_detects_180_day_gap():
    summary = analyse_channel(
        ActivityObservation("instagram", [datetime(2026, 3, 21, tzinfo=timezone.utc)]),
        now=NOW,
    )
    assert summary.last_post_days == 180
    assert summary.inactivity_band == "180_364_DAYS"
    assert summary.historically_active is False


def test_activity_detects_historical_two_posts_per_week():
    dates = [
        datetime(2026, 9, 10, tzinfo=timezone.utc),
        datetime(2026, 9, 3, tzinfo=timezone.utc),
    ] + [datetime(2026, 7, 1, tzinfo=timezone.utc)] * 0
    summary = analyse_channel(ActivityObservation("facebook", dates), now=NOW)
    assert summary.post_count_90d == 2
    assert summary.historical_posts_per_week > 0


def test_scores_activity_and_gap():
    summary = analyse_channel(
        ActivityObservation(
            "instagram",
            [
                datetime(2026, 3, 21, tzinfo=timezone.utc),
                datetime(2026, 3, 14, tzinfo=timezone.utc),
                datetime(2026, 3, 7, tzinfo=timezone.utc),
                datetime(2025, 11, 1, tzinfo=timezone.utc),
            ],
        ),
        now=NOW,
    )
    assert historical_activity_score([summary]) > 0
    assert social_gap_from_activity([summary]) == 90.0


def test_unknown_activity_is_not_verified():
    summary = analyse_channel(ActivityObservation("tiktok", []), now=NOW)
    assert summary.inactivity_band == "NOT_VERIFIED"
    assert social_gap_from_activity([summary]) == 0.0


def test_inactivity_bands():
    assert inactivity_band(30) == "UNDER_60_DAYS"
    assert inactivity_band(90) == "90_119_DAYS"
    assert inactivity_band(365) == "365_PLUS_DAYS"
