# NahaLabs Reactivate v0.20 — AI Video Provider Adapter

## Goal
Connect the production-job contract to KIE's asynchronous AI video API without exposing secrets in the frontend or pretending a task is complete before KIE reports success.

## Provider
KIE API using the unified `/api/v1/jobs/createTask` endpoint and Veo 3.1 (`veo-3-1`). KIE generation is asynchronous; Reactivate stores the returned task ID and reconciles status through `/api/v1/jobs/recordInfo` or a future callback workflow.

## Guardrails
- `KIE_API_KEY` is server-side only.
- Submission means `IN_PRODUCTION`, not `RENDERED`.
- Only a successful provider result with a result URL can mark a job `RENDERED`.
- Provider failures become `BLOCKED` with the error retained.
- v0.20 uses an 8-second provider clip; longer-form assembly is a later stage.
- Local FFmpeg remains available as a free deterministic preview path.
