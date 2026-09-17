# NahaLabs Reactivate v0.23 — Publishing Engine

## Objective
Move completed media from `READY_TO_PUBLISH` into an auditable, platform-specific publishing queue.

## Scope
- Build publishing packages from production jobs.
- Store platform, caption, hashtags, media URL, schedule time, provider and status.
- Support QUEUED/SCHEDULED/PUBLISHING/PUBLISHED/FAILED/CANCELLED.
- Provide a provider-neutral dry-run publisher for local verification.
- Keep real platform publishing behind authenticated adapters; never fake a live post.

## API
- `GET /api/v1/prospects/{prospect_id}/publishing-jobs`
- `POST /api/v1/production-jobs/{job_id}/publish-package`
- `PATCH /api/v1/publishing-jobs/{publish_job_id}`
- `POST /api/v1/publishing-jobs/{publish_job_id}/publish`

## Exit criteria
A rendered/ready job can become a scheduled publishing record, and the dry-run path produces a deterministic published URL without contacting a social platform.
