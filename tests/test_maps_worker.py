from backend.app.maps_worker import _text


def test_text_helper_returns_none_for_empty_locator():
    class Locator:
        def inner_text(self, timeout=0):
            return "   "

    assert _text(Locator()) is None


def test_text_helper_strips_text():
    class Locator:
        def inner_text(self, timeout=0):
            return "  Example Salon  "

    assert _text(Locator()) == "Example Salon"
