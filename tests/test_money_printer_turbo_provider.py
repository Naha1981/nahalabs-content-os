from app.providers.contracts import GenerationRequest
from app.providers.money_printer_turbo import MoneyPrinterTurboProvider


def test_mpt_disabled_does_not_support_video():
    provider = object.__new__(MoneyPrinterTurboProvider)
    provider.enabled = False
    assert provider.supports("generate_video") is False


def test_mpt_subject_preserves_creative_brief():
    request = GenerationRequest(
        operation="generate_video",
        prompt="Business: Demo\nHook: Try our new menu",
    )
    subject = MoneyPrinterTurboProvider._subject(request)
    assert "Demo" in subject
    assert "Try our new menu" in subject
