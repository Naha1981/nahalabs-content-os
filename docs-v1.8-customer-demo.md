# v1.8 — Customer Demo Frontend

v1.8 adds the customer-facing restaurant demo surface on top of the production backend.

## Customer journey

Create/identify business → upload/record footage → generate content pack → review assets → approve → connect social accounts → preflight → schedule/publish → analytics.

The frontend intentionally ships with a demo mode so NahaLabs can demonstrate the product before provider credentials and customer social accounts are connected. Live integration should replace demo actions with the existing FastAPI endpoints.

## Product boundary

No generated asset may publish merely because generation or quality checks succeeded. The existing approval grant remains the authorization boundary. Zernio preflight should run before a publish request, and webhook events should be deduplicated and processed asynchronously.
