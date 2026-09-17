# Reactivate v0.18
Content Production Pipeline for NahaLabs Reactivate.

Backend: FastAPI + SQLite. Frontend: React/Vite.

The production layer creates auditable briefs from human-reviewable content assets. It does not claim to render videos.

Run backend from this directory with the project's existing requirements and `uvicorn backend.app.main:app --reload`.
Run tests with `python -m pytest -q`.
