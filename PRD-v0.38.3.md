# Reactivate v0.38.3

## Purpose
Fix local browser-to-API connectivity on Windows when Uvicorn is bound to `127.0.0.1`.

## Changes
- Frontend API base URL uses `http://127.0.0.1:8000` instead of `http://localhost:8000`.
- Backend health version label updated to `0.38.3`.
- No business logic changed.
