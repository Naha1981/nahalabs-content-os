# NahaLabs Reactivate v0.34

Reactivate v0.34 adds the Automation Scheduler & Job Runner. It persists operational schedules and execution history and exposes safe manual execution endpoints.

The scheduler is an orchestration layer, not a claim of live external automation. Social discovery/publishing still requires real provider access and credentials.

## Run backend
```bash
uvicorn backend.app.main:app --reload
```

## Test
```bash
pytest -q
```
