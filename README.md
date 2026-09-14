# NahaLabs AutoPost — Content Operating System

NahaLabs AutoPost is the execution layer for the NahaLabs content operating system.

It combines the existing NahaLabs content intelligence, generation, media and analytics stack with the publishing model proven by OpenPost: one source publication, platform-specific renditions, durable scheduling, connected accounts, media management, analytics and automation.

## What we are keeping

The existing NahaLabs repository is already valuable and is **not** being thrown away:

- `app/` — FastAPI backend, domain models, content intelligence, strategy, publishing, quality gates and workers.
- `alembic/` — existing database migration history.
- `frontend/` — existing NahaLabs Next.js application.
- `video-factory/` — NahaLabs vertical-video production pipeline.
- `services/` — media intelligence and strategy contracts.
- `tests/` — existing regression coverage.
- KIE.ai, Higgsfield and FFmpeg provider/media layers.
- Publishing preflight, approval and reconciliation logic.

The pre-migration repository is preserved at branch:

`backup/pre-autopost-migration-2026-09-14`

## What we are adopting from OpenPost

OpenPost gives us the right execution concepts rather than something we should blindly duplicate:

- publication as the canonical source object
- independent destination renditions
- social sets / reusable account groups
- durable scheduled queue
- media library and creative tooling
- workspace/account boundaries
- API + CLI + MCP surfaces
- provider adapters and provider-readiness checks
- auditability and retry semantics

OpenPost is AGPL-3.0-only, so we will preserve its license obligations and keep any direct OpenPost-covered implementation clearly identified. We will not silently turn AGPL code into proprietary NahaLabs code.

## Target AutoPost flow

`Business / campaign context → Content Intelligence → Creative Brief → KIE.ai / media generation → Quality Gate → AutoPost Publication → platform renditions → approval → schedule → publish → analytics → learning`

The key design decision is that **NahaLabs owns the intelligence**, while AutoPost owns the execution lifecycle.

## Upstream reference

OpenPost: https://github.com/getopenpost/openpost

See `docs/autopost-openpost-integration.md` for the integration boundary and next implementation steps.
