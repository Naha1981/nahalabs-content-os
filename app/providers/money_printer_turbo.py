from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.providers.contracts import GenerationRequest, GenerationResult
from app.services.storage import S3Storage


class MoneyPrinterTurboProvider:
    """Optional local/sidecar adapter for MoneyPrinterTurbo's video pipeline.

    NahaLabs owns the creative brief, tenant boundary, approval flow, storage,
    quality gates, publishing and analytics. MPT is used only as an execution engine.
    """

    name = "moneyprinterturbo"

    def __init__(self) -> None:
        s = get_settings()
        self.enabled = s.mpt_enabled
        self.root = Path(s.mpt_root).expanduser()
        self.python = s.mpt_python
        self.timeout = s.mpt_timeout_seconds
        self.storage = S3Storage()

    def supports(self, operation: str) -> bool:
        return self.enabled and operation == "generate_video"

    async def submit(self, request: GenerationRequest) -> GenerationResult:
        if not self.enabled:
            raise RuntimeError("MoneyPrinterTurbo provider is disabled")
        if not self.root.exists():
            raise RuntimeError(f"MoneyPrinterTurbo root does not exist: {self.root}")

        task_id = str(request.metadata.get("asset_id") or UUID(int=0))
        with tempfile.TemporaryDirectory(prefix="nahalabs-mpt-") as td:
            workdir = Path(td)
            local_materials = await self._download_materials(request.media_urls, workdir)
            command = [
                self.python,
                "cli.py",
                "--video-subject",
                self._subject(request),
                "--video-aspect",
                request.aspect_ratio,
                "--task-id",
                task_id,
            ]
            if local_materials:
                command.extend([
                    "--video-source",
                    "local",
                    "--video-materials",
                    ",".join(map(str, local_materials)),
                ])

            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=self.root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout
            )
            if process.returncode != 0:
                detail = (stderr or stdout).decode("utf-8", errors="replace")[-2000:]
                raise RuntimeError(
                    f"MoneyPrinterTurbo failed ({process.returncode}): {detail}"
                )

            result = self._parse_result(stdout.decode("utf-8", errors="replace"))
            video_path = self._find_video(result)
            if not video_path.exists() or video_path.stat().st_size == 0:
                raise RuntimeError(
                    "MoneyPrinterTurbo completed without a non-empty video"
                )

            business_id = UUID(str(request.metadata["business_id"]))
            asset_id = UUID(str(request.metadata["asset_id"]))
            key = self.storage.object_key(business_id, asset_id, video_path.name)
            self.storage.upload_file(str(video_path), key, "video/mp4")
            output_url = self.storage.presigned_get(key, expiry=3600)

            return GenerationResult(
                provider=self.name,
                provider_job_id=task_id,
                status="completed",
                output_urls=(output_url,),
                model="moneyprinterturbo",
                metadata={"mpt_result": result, "storage_key": key},
            )

    async def status(self, provider_job_id: str) -> GenerationResult:
        raise RuntimeError(
            "MoneyPrinterTurbo jobs complete during submit; status polling is not supported"
        )

    async def _download_materials(
        self, urls: tuple[str, ...], directory: Path
    ) -> list[Path]:
        paths: list[Path] = []
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            for index, url in enumerate(urls[:20]):
                if not url.startswith(("https://", "http://")):
                    continue
                response = await client.get(url)
                response.raise_for_status()
                suffix = ".mp4"
                content_type = response.headers.get("content-type", "")
                if "quicktime" in content_type:
                    suffix = ".mov"
                elif "webm" in content_type:
                    suffix = ".webm"
                path = directory / f"source-{index}{suffix}"
                path.write_bytes(response.content)
                paths.append(path)
        return paths

    @staticmethod
    def _subject(request: GenerationRequest) -> str:
        return (
            "Create a short-form social video from this NahaLabs production brief. "
            "Preserve factual claims and do not invent prices, testimonials, awards, "
            "or results.\n\n" + request.prompt
        )[:8000]

    @staticmethod
    def _parse_result(stdout: str) -> dict[str, Any]:
        for line in reversed(stdout.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        raise RuntimeError("MoneyPrinterTurbo did not return a JSON result")

    @staticmethod
    def _find_video(result: dict[str, Any]) -> Path:
        payload = result.get("result") if isinstance(result.get("result"), dict) else result
        videos = payload.get("videos") if isinstance(payload, dict) else None
        if not videos:
            raise RuntimeError("MoneyPrinterTurbo result did not contain videos")
        candidate = Path(str(videos[0])).expanduser()
        if not candidate.is_absolute():
            candidate = Path.cwd() / candidate
        return candidate.resolve()
