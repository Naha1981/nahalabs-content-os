import uuid
import pytest
from app.providers.contracts import GenerationResult
from app.services.content_factory import ContentFactory

class FakeProvider:
    name = "fake"
    def supports(self, operation): return operation == "generate_video"
    async def submit(self, request):
        return GenerationResult(provider=self.name, provider_job_id="job-1", status="queued", model="fake")
    async def status(self, provider_job_id):
        return GenerationResult(provider=self.name, provider_job_id=provider_job_id, status="completed", model="fake", output_urls=("https://example.test/video.mp4",))

class FakeRouter:
    async def submit(self, request): return await FakeProvider().submit(request)

@pytest.mark.asyncio
async def test_factory_submits_asset():
    result = await ContentFactory(router=FakeRouter()).submit_asset(
        business_id=uuid.uuid4(), creative_brief_id=uuid.uuid4(), prompt="Create a restaurant reel"
    )
    assert result.status == "provider_queued"
    assert result.provider_job_id == "job-1"

def test_quality_gate_passes_clean_asset():
    result = ContentFactory(router=FakeRouter()).quality_check(output_present=True, metadata={"aspect_ratio":"9:16"})
    assert result.passed is True
