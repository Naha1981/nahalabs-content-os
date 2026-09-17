import httpx

from backend.app.enrichment import enrich_business, inspect_website


class FakeClient:
    def get(self, url):
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            headers={"content-type": "text/html; charset=utf-8"},
            text='''<html><body><a href="https://instagram.com/demo">Instagram</a><a href="https://www.facebook.com/demo">Facebook</a><p>Call +27 11 123 4567</p></body></html>''',
        )


def test_inspect_website_extracts_public_social_links_and_phone():
    result = inspect_website("https://example.com", client=FakeClient())
    assert result["status"] == "OBSERVED"
    assert result["social_urls"]["instagram"] == "https://instagram.com/demo"
    assert result["social_urls"]["facebook"] == "https://www.facebook.com/demo"
    assert result["phone"] == "+27 11 123 4567"
    assert len(result["evidence"]) == 4


def test_enrich_business_without_website_does_not_guess():
    result = enrich_business({"name": "Demo", "google_url": "https://maps.google.com/demo"})
    assert result["enrichment_status"] == "NO_WEBSITE_FOUND"
    assert result["social_urls"] == {}
    assert result["evidence"] == []
