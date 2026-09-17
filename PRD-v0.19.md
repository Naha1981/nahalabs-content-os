# NahaLabs Reactivate v0.19 — Media Rendering Worker

## Objective
Turn an approved content production brief into a real media artifact while keeping the renderer provider-agnostic.

## User flow
Approved content asset → production brief → render request → renderer → real MP4 → RENDERED → ready for the next publishing stage.

## v0.19 scope
- Local FFmpeg preview renderer.
- Real H.264/AAC MP4 output in a social-friendly 9:16 frame.
- Persistent renderer, error and rendered-at metadata.
- Media served from `/media/...` by the API.
- UI render action, playback preview and MP4 link.
- Automatic content asset transition to `PRODUCED` only after an actual file exists.

## Honesty boundary
The local renderer is explicitly a deterministic preview generator, not an AI UGC/video model. It uses the production brief's hook, voiceover and CTA as on-screen text over a generated background. No external AI provider is claimed or simulated.

## Future provider boundary
The renderer adapter can later be replaced or extended with KIE.ai, Remotion/FFmpeg pipelines, or another video/UGC provider without changing the production-job contract.

## States
`BRIEF_READY → IN_PRODUCTION → RENDERED → READY_TO_PUBLISH → PUBLISHED`

A failed render becomes `BLOCKED` and stores `render_error`; it never becomes `RENDERED` without a real file.
