# Publishing and approval layer

Consequential publishing actions require an explicit scoped approval grant. The API does not accept a generic boolean `approved`; it records who granted authority, scope, platforms, content types, and optional expiry.

Flow:

1. Business creates/ensures one Zernio profile.
2. UI requests `/social/connect-url?business_id=...&platform=...`.
3. Customer completes OAuth in Zernio's hosted flow.
4. Zernio webhooks synchronize connected-account state.
5. Customer reviews exact asset/platform/account/caption/time in the frontend.
6. Customer creates a scoped approval grant.
7. Publishing job is created with `Idempotency-Key`.
8. Publishing worker consumes queued/scheduled jobs and calls the Zernio adapter.
9. Zernio webhook events update the domain state.
10. UI shows an action receipt.

Never store Zernio OAuth secrets in our database. Zernio remains an infrastructure adapter.
