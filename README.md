# NahaLabs Content OS Backend

Production-oriented backend foundation for the NahaLabs Content OS.

## v0.3

Adds the generation boundary and rendering layer:

- provider-agnostic `GenerationProvider` contract
- configurable KIE.ai provider adapter
- `GenerationRouter`
- `CreativeBrief` and `GeneratedAsset` persistence
- per-brief generation API
- FFmpeg renderer contract/implementation
- migration `0002_generation`

KIE endpoint paths are deliberately configuration-driven because provider APIs can evolve. Domain code never depends on provider-specific IDs or payload shapes.

## Run

```bash
cp .env.example .env
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
pytest
```

## Architecture

Next.js → FastAPI → PostgreSQL / Redis / S3 → SQS → workers → generation providers / FFmpeg → approval → publishing adapter.

## v1.0 Publishing Worker

The publishing worker claims approved queued/scheduled jobs with PostgreSQL row locks, uploads the final media to Zernio, creates/schedules the platform post, records the external post ID, and relies on Zernio webhooks for final platform status reconciliation. Failed jobs use bounded exponential retry and become `failed` after three attempts.

Run one polling pass:

```bash
python -m app.workers.publishing_worker --once
```

Run continuously:

```bash
python -m app.workers.publishing_worker
```

## v1.3 Content Intelligence Engine

The adaptive layer can now turn Brand DNA and measured social performance into a persisted 10–50 brief content plan:

`POST /api/v1/content-intelligence/businesses/{business_id}/plan`

Preview without persistence:

`GET /api/v1/content-intelligence/businesses/{business_id}/preview?asset_count=10`

Each brief records evidence, winning-pattern context, platform priority, experiment assignment, and conditional Higgsfield polish metadata.

## v1.4 — Creative Generation Orchestrator

v1.4 turns creative briefs into a provider-neutral production state machine:

`queued → provider_processing → polishing (optional) → quality_review`

Provider outputs are immediately persisted to private S3-backed `MediaAsset` records before the asset can reach quality review. KIE remains the default generation route; Higgsfield is an optional final polish stage.

Run a single generation-worker pass with:

`python -m app.workers.generation_worker --once`

## v1.6
Publishing now has a preflight and explicit approval boundary. Jobs cannot reach the publishing worker until internal quality passes, Zernio dry-run validation passes, and an authorized user approves the action.
