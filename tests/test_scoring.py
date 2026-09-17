from backend.app.models import BusinessProspect, SocialChannel
from backend.app.scoring import opportunity_score, social_gap_score, grade


def make_prospect(days: int) -> BusinessProspect:
    return BusinessProspect(
        name="Demo Business",
        city="Johannesburg",
        website="https://example.com",
        category="service",
        health_score=90,
        content_dependency_score=90,
        monetization_score=80,
        reputation_score=90,
        historical_activity_score=85,
        audience_score=70,
        competitive_gap_score=80,
        contactability_score=90,
        social_channels=[
            SocialChannel(
                platform="instagram",
                url="https://instagram.com/example",
                followers=2500,
                posts_last_90d=0,
                posts_last_365d=8,
                last_meaningful_post_days=days,
            )
        ],
    )


def test_social_gap_180_days_is_strong():
    assert social_gap_score(make_prospect(180)) == 90


def test_social_gap_under_60_days_is_zero():
    assert social_gap_score(make_prospect(30)) == 0


def test_opportunity_score_is_deterministic():
    prospect = make_prospect(180)
    assert opportunity_score(prospect) == opportunity_score(prospect)


def test_grade_boundaries():
    assert grade(95) == "A+"
    assert grade(85) == "A"
    assert grade(75) == "B"
