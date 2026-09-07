# NahaLabs Content OS v1.9 — Demo & Deployment Readiness

v1.9 is intentionally the final MVP engineering pass. It packages the customer demo frontend with a safe demo/live switch and a deployable frontend container.

## Demo mode

Set `NEXT_PUBLIC_DEMO_MODE=true`. The UI uses local demo state and never calls the API. This is the recommended mode for restaurant demonstrations before provider credentials are configured.

## Live mode

Set `NEXT_PUBLIC_DEMO_MODE=false` and `NEXT_PUBLIC_API_BASE_URL` to the FastAPI origin. The frontend can then use the API client in `frontend/lib/api.ts`. Authentication/token acquisition should be wired to Cognito before enabling production live mode.

## Production checklist

- Cognito user pool + app client configured.
- PostgreSQL/Supabase configured and migrations applied through `0010_publishing_hardening`.
- Redis configured.
- Private S3 bucket configured.
- KIE credentials configured with cost limits.
- Zernio API key and webhook secret configured.
- Zernio webhook endpoint configured with only required event groups/events.
- API CORS origin changed from the default demo domain to the real frontend origin.
- SQS queues configured for generation/media workloads.
- Workers deployed separately from the API.
- Secrets stored in the deployment secret manager, never in frontend environment variables.
- Test a real restaurant with one source video before broad rollout.

## Zernio operational notes

Zernio currently documents webhooks as event notifications rather than a complete source-of-truth sync. The backend therefore keeps reconciliation in addition to webhooks. Webhook handlers must verify `X-Zernio-Signature`, deduplicate using the event ID, acknowledge quickly, and process heavier work asynchronously.

Zernio currently offers dry-run post validation under `/v1/tools/validate/post`; use it before creating publishing jobs. The API also supports scheduled posts and analytics.
