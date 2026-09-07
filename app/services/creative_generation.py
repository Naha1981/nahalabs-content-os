from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from uuid import UUID
import tempfile
from pathlib import Path
import uuid
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Business, ContentPack, CreativeBrief, GeneratedAsset, SourceMedia, MediaAsset
from app.providers.contracts import GenerationRequest
from app.services.generation_router import GenerationRouter
from app.services.storage import S3Storage

@dataclass(frozen=True)
class GenerationPlan:
    operation: str
    prompt: str
    media_urls: tuple[str, ...]
    aspect_ratio: str
    duration_seconds: int | None
    polish_requested: bool
    polish_prompt: str | None


def build_prompt(brief: CreativeBrief, business: Business) -> str:
    direction = brief.visual_direction or {}
    copy = brief.copy_direction or {}
    parts = [
        f"Business: {business.name}",
        f"Industry: {business.industry or 'general business'}",
        f"Objective: {brief.objective}",
        f"Angle: {brief.angle}",
        f"Hook: {brief.hook}",
        f"Audience: {brief.audience or 'local customers'}",
        f"CTA: {brief.cta or 'clear, truthful call to action'}",
        f"Visual direction: {direction}",
        f"Copy direction: {copy}",
        "Create original, brand-safe content. Do not invent testimonials, prices, claims, awards, or customer results.",
    ]
    return "\n".join(parts)


async def build_generation_plan(db: AsyncSession, asset: GeneratedAsset) -> GenerationPlan:
    brief = await db.get(CreativeBrief, asset.creative_brief_id)
    if not brief:
        raise ValueError("Creative brief not found")
    pack = await db.get(ContentPack, asset.content_pack_id)
    if not pack:
        raise ValueError("Content pack not found")
    business = await db.get(Business, pack.business_id)
    if not business:
        raise ValueError("Business not found")

    media_urls: list[str] = []
    if pack.source_media_id:
        source = await db.get(SourceMedia, pack.source_media_id)
        if source:
            media = await db.get(MediaAsset, source.media_asset_id)
            if media:
                try:
                    media_urls.append(S3Storage().presigned_get(media.storage_key, expiry=600))
                except Exception:
                    # Generation can still work without source footage for fully generative briefs.
                    pass

    metadata = asset.asset_metadata or {}
    aspect_ratio = str(metadata.get("aspect_ratio", "9:16"))
    duration = brief.duration_seconds
    polish_requested = bool(metadata.get("polish_requested", False))
    polish_prompt = metadata.get("polish_prompt") or "Premium final polish while preserving the approved creative intent, subject identity, brand rules, and factual claims."
    operation = "generate_image" if asset.asset_type == "image" else "generate_video"
    return GenerationPlan(operation, build_prompt(brief, business), tuple(media_urls), aspect_ratio, duration, polish_requested, polish_prompt)


async def persist_provider_output(db: AsyncSession, asset: GeneratedAsset, output_url: str, business_id: UUID) -> tuple[UUID, str]:
    if not output_url.startswith(("https://", "http://")):
        raise ValueError("Provider output URL must use HTTP(S)")
    async with httpx.AsyncClient(timeout=180, follow_redirects=True) as client:
        response = await client.get(output_url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "application/octet-stream").split(";")[0]
        suffix = ".mp4" if "video" in content_type else ".png" if "image" in content_type else ".bin"
        with tempfile.TemporaryDirectory(prefix="nahalabs-output-") as td:
            local = Path(td) / f"output{suffix}"
            local.write_bytes(response.content)
            media_id = uuid.uuid4()
            storage = S3Storage()
            key = storage.object_key(business_id, media_id, local.name)
            storage.upload_file(str(local), key, content_type)
            media = MediaAsset(
                id=media_id, business_id=business_id, type=asset.asset_type, storage_key=key,
                mime_type=content_type, size_bytes=len(response.content),
                asset_metadata={"source": "generation_provider", "provider_output_url": output_url},
            )
            db.add(media)
            await db.flush()
            asset.media_asset_id = media.id
            return media.id, key


class CreativeGenerationOrchestrator:
    """Runs the provider-neutral production state machine for one GeneratedAsset."""
    def __init__(self, router: GenerationRouter | None = None) -> None:
        self.router = router or GenerationRouter()

    async def submit(self, db: AsyncSession, asset: GeneratedAsset) -> dict[str, Any]:
        plan = await build_generation_plan(db, asset)
        result = await self.router.submit(GenerationRequest(
            operation=plan.operation,
            prompt=plan.prompt,
            media_urls=plan.media_urls,
            aspect_ratio=plan.aspect_ratio,
            duration_seconds=plan.duration_seconds,
            metadata={"asset_id": str(asset.id), "polish_requested": plan.polish_requested},
        ))
        asset.status = "provider_processing"
        asset.generation_provider = result.provider
        asset.generation_model = result.model
        asset.provider_job_id = result.provider_job_id
        asset.generation_cost = result.estimated_cost
        asset.asset_metadata = {**(asset.asset_metadata or {}), "provider_status": result.status, "source_media_attached": bool(plan.media_urls)}
        return {"status": result.status, "provider": result.provider, "provider_job_id": result.provider_job_id}

    async def poll(self, db: AsyncSession, asset: GeneratedAsset) -> dict[str, Any]:
        if not asset.provider_job_id or not asset.generation_provider:
            raise ValueError("Asset has no provider job")
        result = await self.router.status(asset.generation_provider, asset.provider_job_id)
        metadata = {**(asset.asset_metadata or {}), "provider_status": result.status, "output_urls": list(result.output_urls)}
        asset.asset_metadata = metadata
        if result.status.lower() in {"failed", "error", "cancelled", "canceled"}:
            asset.status = "failed"
            return {"status": "failed", "provider_status": result.status}
        if result.status.lower() not in {"completed", "complete", "succeeded", "success", "done"} or not result.output_urls:
            asset.status = "provider_processing"
            return {"status": "processing", "provider_status": result.status}

        plan = await build_generation_plan(db, asset)
        if plan.polish_requested and asset.generation_provider != "higgsfield":
            polish = await self.router.submit(GenerationRequest(
                operation="polish_video",
                prompt=plan.polish_prompt or "Final premium polish.",
                media_urls=(result.output_urls[0],),
                aspect_ratio=plan.aspect_ratio,
                duration_seconds=plan.duration_seconds,
                metadata={"asset_id": str(asset.id), "source_provider": result.provider, "final_polish": True},
            ))
            asset.status = "polishing"
            asset.generation_provider = polish.provider
            asset.generation_model = polish.model
            asset.provider_job_id = polish.provider_job_id
            asset.generation_cost = (asset.generation_cost or 0) + polish.estimated_cost
            asset.asset_metadata = {**metadata, "pre_polish_output_url": result.output_urls[0], "polish_provider_job_id": polish.provider_job_id}
            return {"status": "polishing", "provider": polish.provider}

        pack = await db.get(ContentPack, asset.content_pack_id)
        if not pack:
            raise ValueError("Content pack not found")
        media_id, storage_key = await persist_provider_output(db, asset, result.output_urls[0], pack.business_id)
        asset.status = "quality_review"
        asset.asset_metadata = {**metadata, "final_output_url": result.output_urls[0], "final_provider": result.provider, "storage_key": storage_key, "media_asset_id": str(media_id)}
        return {"status": "quality_review", "output_url": result.output_urls[0], "media_asset_id": str(media_id)}
