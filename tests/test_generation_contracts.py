from uuid import uuid4
from app.domain.contracts import GenerationRequest

def test_generation_request_is_provider_agnostic():
    req = GenerationRequest(business_id=uuid4(), creative_brief_id=uuid4(), asset_kind='video', prompt='premium burger commercial')
    assert req.aspect_ratio == '9:16'
    assert req.asset_kind == 'video'
