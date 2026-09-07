# v2.0 — Video Factory

The Video Factory is the first end-to-end content-production module of the Content OS:
topic (or product URL) in, quality-gated vertical video out — one workflow, one repo.

It lives in `video-factory/` as a self-contained Next.js app (App Router, TypeScript,
Tailwind, Prisma/SQLite) so it can run standalone today and plug into the backend
content-engine chain later.

## Pipeline

```
input (topic | product URL)
  1. research      — live web search (6 sources) distilled into a research brief,
                     or product-page reading for UGC ad mode
  2. script        — scene-by-scene script (narration / on-screen text / visual prompt),
                     duration-aware scene count, hook-first structure
  3. visuals       — one vertical 9:16 image per scene (2 in parallel)
  4. narration     — TTS voice track per scene (sequential, quota-aware retries)
  5. captions      — word-level timings, re-scaled when the browser probes real
                     audio durations (WhisperX-style alignment concept)
  6. quality gate  — technical checks + VLM frame review + ASR speech match
  7. render/export — in-browser WebM render, SRT, timeline JSON, Remotion composition
```

## Statuses

Project status mirrors the worker vocabulary: `queued -> researching -> scripting ->
visualizing -> narrating -> subtitling -> quality_review -> approved_ready |
quality_failed | failed`. The runner is idempotent — completed steps skip, failed assets
retry, the quality gate re-runs. `POST /api/projects/{id}/run` resumes.

## Quality gate

Same philosophy as `app/services/quality_engine.py`: passing quality makes an asset
eligible, it never grants publish permission.

Checks: visuals present, narration present, scene count, pacing vs target, vision review
(VLM scores each frame 1-10 against its visual prompt), speech match (ASR transcript of
scene 1 compared to the script). Overall score = mean of technical + visual + narration
scores; pass requires no hard failures and overall >= 0.7.

## Provider routing

`video-factory/src/lib/providers.ts` — a `GenerationRouter` with operations
`web.search | web.read | text.generate | image.generate | speech.synthesize |
speech.transcribe | vision.analyze`, route decisions, and replaceable adapters —
the same contract philosophy as `app/providers` + `app/services/generation_router.py`.

Default route: the z-ai SDK. GPU-box route: set `VIDEO_FACTORY_IMAGE_ENDPOINT` to any
HTTP gateway implementing `POST {prompt,size} -> {image_base64}` (wrap ComfyUI, Wan 2.2,
or HunyuanVideo however you like) and `image.generate` re-routes with no other changes.
There is deliberately no fake GPU-model code in this repo.

## API surface (module-local)

- `POST /api/projects` — create + launch pipeline (topic or UGC mode)
- `GET /api/projects` — list with per-project asset readiness
- `GET /api/projects/{id}` — full detail (scenes, events, quality) for live polling
- `DELETE /api/projects/{id}` — delete project + generated assets
- `POST /api/projects/{id}/run` — idempotent resume / retry
- `GET /api/projects/{id}/export?format=srt|json|remotion` — exports
- `PATCH /api/scenes/{id}` — edit narration / on-screen text; audio-duration probe
  re-scales caption timings server-side
- `POST /api/scenes/{id}/regenerate` — per-scene image or narration regeneration

## Data model

`VideoProject` (brief-level: topic, mode, platform, style, voice, duration target,
research/script/quality JSON) -> `VideoScene` (narration, on-screen text, visual prompt,
image + audio asset status/URLs, word timings, VLM score) -> `PipelineEvent` (log).

## Rendering story (honest version)

- In-browser: canvas renderer with Ken Burns motion, crossfades, karaoke captions, synced
  narration — and a real WebM export via MediaRecorder (records in real time).
- Studio-grade: the Remotion export emits a self-contained composition (`.tsx`) of the
  same timeline; render it anywhere Remotion is installed for an MP4.
- The timeline itself is data (timeline JSON) — the HyperFrames/OpenMontage "video as
  code" approach, ready for other render targets.

## Integration hooks (next steps)

- Swap the z-ai generation route for the backend's KIE provider via the router contract.
- Feed `approved_ready` projects into `CreativeBrief`/`GeneratedAsset` and let the
  existing publishing pipeline (preflight -> approval -> Zernio) take over.
- Reuse `GenerationJob` with `job_type='video_factory.render'` for worker-based renders.
