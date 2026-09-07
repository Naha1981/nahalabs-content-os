from app.services.publishing_preflight import _normalize


def test_normalize_valid_result():
    result = {"valid": True, "message": "No validation issues found.", "warnings": [{"platform": "instagram", "warning": "near limit"}]}
    normalized = _normalize(result)
    assert normalized["valid"] is True
    assert normalized["errors"] == []
    assert len(normalized["warnings"]) == 1


def test_normalize_invalid_result():
    result = {"valid": False, "errors": [{"platform": "tiktok", "error": "media missing"}]}
    normalized = _normalize(result)
    assert normalized["valid"] is False
    assert normalized["errors"][0]["platform"] == "tiktok"
