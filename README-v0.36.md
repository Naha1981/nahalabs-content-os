# Reactivate v0.36
Autonomous scheduler worker for the Reactivate operating system.

Backend: FastAPI + SQLite + pure-Python worker.

Run once:
`python -m backend.app.worker --once`

Run continuously:
`python -m backend.app.worker --interval 30`

Sandbox validation includes scheduler/worker tests. Browser-rendered QA remains for Windows.
