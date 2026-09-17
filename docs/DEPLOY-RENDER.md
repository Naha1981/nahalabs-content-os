# NahaLabs Reactivate — Render deployment

This Blueprint deploys two free Render services:

- `nahalabs-reactivate-api`: FastAPI Docker web service
- `nahalabs-reactivate-web`: Vite/React static site

The API listens on Render's `$PORT`, exposes `/health`, `/api/v1/*`, and `/media/*`, and reports Playwright/Chromium availability from `/health`.

The static frontend reads `VITE_API_BASE_URL` at build time. Render supplies the API hostname through `fromService`; the frontend adds `https://` when necessary and never appends `/api`.

After the first Blueprint deploy, set the API service's `REACTIVATE_CORS_ORIGINS` to the exact static site URL and redeploy the API.

The free filesystem is ephemeral, so SQLite and generated media are disposable until storage is migrated to an external database/object store or a plan with persistent storage.
