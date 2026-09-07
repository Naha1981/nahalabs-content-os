# Publishing Worker

## Responsibility

The API creates an approved `PublishingJob`; the worker performs the consequential provider action. This keeps provider latency and retries out of the request path.

## Execution

1. Claim `queued`/due jobs with `FOR UPDATE SKIP LOCKED`.
2. Increment attempts and mark `publishing`.
3. Validate the connected social account and generated media.
4. Download private media from S3.
5. Upload media to Zernio.
6. Create an immediate or scheduled Zernio post.
7. Persist the external post ID.
8. Wait for Zernio webhook events for authoritative per-platform terminal state.
9. Retry transient worker/provider failures up to three times.
10. Emit a failure state after the retry budget is exhausted.

Zernio documents `post.published`, `post.failed`, `post.partial`, `post.platform.published`, and `post.platform.failed` webhook events, and recommends webhook IDs as deduplication keys. The API's own idempotency key remains the durable identity of the NahaLabs publishing intent.
