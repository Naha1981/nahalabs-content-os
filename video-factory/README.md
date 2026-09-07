# NahaLabs Video Factory

The Video Factory is the v2.0 module of the Content OS: an end-to-end, open-source video
content pipeline that turns a **topic** (or a **product URL** for UGC ads) into a
quality-gated vertical video — in one workflow.

```
topic / product URL
  -> live web research (search + page reading)
  -> script with scene breakdown (hook -> scenes -> CTA)
  -> per-scene AI visuals (vertical 9:16)
  -> TTS narration per scene
  -> word-level karaoke captions
  -> quality gate (technical checks + vision review + speech match)
  -> playable video (in-browser render) + exports (WebM / SRT / timeline JSON / Remotion)
```

It runs as a self-contained Next.js app (App Router + Prisma/SQLite) with the z-ai SDK
doing the generation work server-side, behind the same provider-adapter philosophy as the
backend's `GenerationProvider` / `GenerationRouter` (see `docs-provider-routing.md`).

## Run

```bash
cp .env.example .env
bun install
bun run db:push
bun run dev
```

Open http://localhost:3000 — throw in a topic and watch the pipeline run.

## Modes

- **Topic -> Video** — research the topic on the live web, then script/visualize/narrate it.
- **Product URL -> UGC Ad** — read the product page (like the OpenAI-UGC / Arcads-style
  studios), extract product intelligence, and generate a creator-style UGC ad script.

## Quality gate

Nothing is called *ready* until the gate passes (same semantics as
`app/services/quality_engine.py` — quality passing means eligible, never auto-publish):

- scene visuals present (per-asset status)
- narration tracks present (per-asset status)
- scene count and pacing vs target
- **vision review** — a VLM scores every generated frame 1-10 against its visual prompt
- **speech match** — ASR transcribes scene 1 and scores it against the script

Projects land in `approved_ready` or `quality_failed` (still playable; failed assets can
be retried individually from the storyboard).

## Provider routing

`src/lib/providers.ts` implements a `GenerationRouter` with operations
(`web.search`, `web.read`, `text.generate`, `image.generate`, `speech.synthesize`,
`speech.transcribe`, `vision.analyze`) and route decisions.

The default route is the z-ai SDK. To route image generation to your own GPU box
(ComfyUI, Wan 2.2, HunyuanVideo — anything you can wrap in a tiny HTTP gateway), set:

```
VIDEO_FACTORY_IMAGE_ENDPOINT=http://your-gpu-box:8188/video-factory/image
```

The endpoint contract is `POST { prompt, size }` -> `{ image_base64 }`. Until then,
generation stays on the default route — the domain never sees provider payloads.

## Exports

- **WebM** — real in-browser render (canvas + audio capture via MediaRecorder)
- **SRT** — caption file with word-level-derived cue timings
- **timeline JSON** — the full declarative timeline (scenes, words, assets)
- **Remotion composition (.tsx)** — the same timeline as Remotion source for a
  studio-grade MP4 render on any machine with Remotion installed (the HyperFrames /
  "video as code" approach)

## Data model (Prisma / SQLite)

`VideoProject` -> `VideoScene` (narration, on-screen text, visual prompt, image/audio
asset status + URLs, word timings) -> `PipelineEvent` (activity log). Project status
vocabulary mirrors the backend workers:
`queued -> researching -> scripting -> visualizing -> narrating -> subtitling -> quality_review
-> approved_ready | quality_failed | failed`.

The pipeline is **idempotent and resumable**: completed steps skip, failed assets retry,
the quality gate re-runs. Per-scene regeneration (image / narration) and narration
editing are supported from the storyboard.
