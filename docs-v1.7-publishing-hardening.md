# v1.7 — Production Publishing Hardening

## Guarantees

1. **Provider idempotency** — every create call gets a stable per-publishing-job `x-request-id` (`PublishingJob.idempotency_key`). Zernio documents a ~5-minute same-request retry window and a separate 24-hour content-hash duplicate guard.
2. **Local idempotency** — `publishing_jobs.idempotency_key` is unique, so application retries cannot create a second local job with the same identity.
3. **Webhook deduplication** — `WebhookEvent.external_event_id` is unique. Zernio webhook deliveries are at-least-once; duplicates are accepted and ignored.
4. **Webhook authenticity** — raw-body HMAC verification uses `X-Zernio-Signature`.
5. **Reconciliation** — the reconciliation worker periodically fetches provider post state for jobs with an external post ID. Webhooks are fast projections; reconciliation repairs missed/late events.
6. **Account reconciliation** — social account sync can be run from the provider account list before publishing operations if a connection is stale.
7. **Scheduled-post control** — draft/scheduled provider posts can be cancelled through the provider DELETE endpoint. Published posts are not treated as deletable.

## State model

`awaiting_preflight -> preflight_failed | awaiting_approval -> queued | scheduled -> publishing -> published | partial | failed`

Provider state is retained separately as `provider_status` and `provider_payload` so provider truth and internal workflow truth remain auditable.

## Operational jobs

- `python -m app.workers.publishing_worker --once`
- `python -m app.workers.publishing_reconciliation_worker --once`

Run the reconciliation worker every 5 minutes in production. Backoff can be added later if provider rate limits become a constraint.
