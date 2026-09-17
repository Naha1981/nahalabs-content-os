# NahaLabs Reactivate v0.17

Prospect intelligence now flows into a Content Studio. Generate three draft assets from prospect evidence and PatternVault structures, edit them, and move them through DRAFT → REVIEW → APPROVED → PRODUCED → PUBLISHED.

## Run
Backend: `uvicorn backend.app.main:app --reload --port 8000`
Frontend: `npm install && npm run dev`
Tests: `pytest -q`

The current generation engine is deterministic and provider-free. It does not claim live LLM generation until a provider is configured.
