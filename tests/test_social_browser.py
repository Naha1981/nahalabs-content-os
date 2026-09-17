from datetime import datetime, timezone

import backend.app.social_browser as sb


class FakeMouse:
    def wheel(self, _x, _y):
        return None


class FakePage:
    def __init__(self):
        self.url = "https://www.instagram.com/acme/"
        self.mouse = FakeMouse()

    def goto(self, *args, **kwargs):
        return None

    def wait_for_timeout(self, _ms):
        return None

    def content(self):
        return '''
        <html><head>
          <meta name="followers" content="1,250 followers">
          <meta property="article:published_time" content="2026-01-01T00:00:00Z">
        </head><body><time datetime="2025-12-01"></time></body></html>
        '''

    def title(self):
        return "Acme | Instagram"


class FakeContext:
    def new_page(self):
        return FakePage()


class FakeBrowser:
    def new_context(self, **_kwargs):
        return FakeContext()

    def close(self):
        return None


class FakeChromium:
    def launch(self, **_kwargs):
        return FakeBrowser()


class FakePlaywright:
    chromium = FakeChromium()


class FakeManager:
    def __enter__(self):
        return FakePlaywright()

    def __exit__(self, *args):
        return False


def test_collect_social_url_uses_rendered_page(monkeypatch):
    monkeypatch.setattr(sb, "sync_playwright", lambda: FakeManager())
    result = sb.collect_social_url(
        "https://www.instagram.com/acme/",
        now=datetime(2026, 9, 17, tzinfo=timezone.utc),
    )
    assert result["status"] == "OBSERVED"
    assert result["platform"] == "instagram"
    assert result["followers"] == 1250
    assert len(result["post_dates"]) == 2
    assert result["activity"]["last_post_days"] == 259


def test_invalid_or_unsupported_url_does_not_attempt_browser():
    result = sb.collect_social_url("https://example.com/acme")
    assert result["status"] == "NOT_VERIFIED"
    assert result["error"] == "Unsupported social platform URL"


def test_batch_keeps_each_platform_separate(monkeypatch):
    monkeypatch.setattr(sb, "collect_social_url", lambda url, **kwargs: {"url": url, "status": "OBSERVED"})
    result = sb.collect_social_urls(
        {"instagram": "https://www.instagram.com/acme/", "facebook": "https://www.facebook.com/acme/"}
    )
    assert set(result) == {"instagram", "facebook"}
