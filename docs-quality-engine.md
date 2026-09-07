# v1.5 — Quality & Approval Engine

Generated media no longer jumps directly toward publishing. The generation worker moves completed assets into a deterministic quality gate.

Pipeline:

`provider output → private S3 → quality check → approved_ready / quality_failed → human approval → Zernio preflight → publish`

Checks include media presence, ffprobe technical evidence where available, aspect ratio, duration, codec, safety flags, visual/brand/platform scores and persisted evidence. Every run is stored in `quality_checks` for auditability.

Publishing remains human-authorized. Quality passing means **eligible for approval**, not permission to publish.

Zernio currently exposes a dry-run `POST /v1/tools/validate/post` endpoint that validates post content without publishing, including platform-specific media/field/character requirements. NahaLabs should call this immediately before creating a publish job once the Zernio adapter exposes it. Zernio also documents webhook signature verification and asynchronous processing requirements.
