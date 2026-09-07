# NahaLabs Content OS v1.6 — Zernio Preflight + Approval Workspace

## Purpose

v1.6 creates a hard publishing safety boundary:

`quality_pass -> platform_preflight -> human approval -> queued/scheduled -> Zernio -> webhook -> analytics`

A generated asset passing the internal quality gate is **not** enough to publish. The customer must have a successful Zernio content preflight and an explicit action approval.

## Endpoints

- `POST /api/v1/publishing/jobs` — creates an `awaiting_preflight` job after checking standing approval authority.
- `POST /api/v1/publishing/jobs/{job_id}/preflight` — uploads the media to Zernio and calls the dry-run post validation pipeline.
- `POST /api/v1/publishing/jobs/{job_id}/approve` — records the approving user and releases the job to the publishing worker.
- `POST /api/v1/publishing/jobs/{job_id}/cancel` — cancels a not-yet-published job.
- `GET /api/v1/publishing/workspace` — returns jobs requiring review or currently in the publish pipeline.

## State machine

`awaiting_preflight -> awaiting_approval -> queued/scheduled -> publishing -> published`

Failure branches:

`awaiting_preflight -> preflight_failed`

`queued/scheduled -> retrying -> failed`

Any not-yet-published state may be cancelled by an authorized user.

## Safety rules

1. Internal quality must be `approved_ready`.
2. Zernio preflight must return `valid=true`.
3. A human with owner/admin/editor membership must explicitly approve the action.
4. The publishing worker only claims jobs with both `approved_at` and `preflight_status=passed`.
5. The existing idempotency key remains the NahaLabs action identity.
6. Zernio webhook event IDs remain deduplication keys; webhook work should stay lightweight and asynchronous.

Zernio's dry-run validation checks platform-specific content rules without publishing, while its webhook guidance recommends fast acknowledgement, signature verification and event-ID deduplication. See the official documentation for the current provider behavior.
