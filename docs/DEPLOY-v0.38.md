# Reactivate v0.38 — Production Hosting Layer

## Purpose
Containerise the FastAPI backend and make it deployable as an HTTPS service. Trigger.dev calls the hosted API; the browser calls the same API.

## Required environment variables
- `REACTIVATE_API_TOKEN`: shared bearer token used by Trigger.dev and protected API routes.
- `REACTIVATE_CORS_ORIGINS`: comma-separated browser origins.
- `REACTIVATE_DB_PATH`: SQLite file path. Default container path is `/app/data/reactivate.db`.
- `REACTIVATE_MEDIA_DIR`: media directory. Default container path is `/app/media`.

## Render
The included `render.yaml` defines a free Docker web service and `/health` health check.

Important: Render's free web-service filesystem is ephemeral. Do **not** treat the container's SQLite database or generated media as durable production storage. Before production use, add a persistent database/storage layer (next phase) or attach an external durable service.

## Local test
`docker build -t nahalabs-reactivate .`
`docker run --rm -p 8000:8000 -e REACTIVATE_API_TOKEN=dev-token nahalabs-reactivate`
Then open `/health` and verify `status: ok`.

## Trigger.dev connection
Set `REACTIVATE_API_URL` to the deployed HTTPS URL and `REACTIVATE_API_TOKEN` to the same token. Trigger.dev remains the scheduler; Reactivate remains the business-logic API.
