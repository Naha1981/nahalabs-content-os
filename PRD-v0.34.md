# Reactivate v0.34 — Automation Scheduler & Job Runner

## Goal
Turn the Daily Operator into scheduled, persisted automation checkpoints while keeping external provider actions credential/network gated and human approval intact.

## Scheduled jobs
- Morning Operator — 06:00 Africa/Johannesburg
- Radar Scan — 06:30
- Follow-up Check — 08:00, 12:00, 16:00
- Campaign Check — hourly
- Publishing Check — every 15 minutes
- Learning Update — 18:00

## Safety
- Jobs are persisted in SQLite.
- Every execution creates a run record.
- Jobs can be enabled/disabled.
- Failures are recorded.
- Radar does not pretend to perform an external scan without network/provider access.
- Publishing remains provider/credential gated.
- No automatic outbound outreach is introduced.

## API
- GET /api/v1/scheduler/jobs
- POST /api/v1/scheduler/jobs/{id}/run
- POST /api/v1/scheduler/jobs/{id}/toggle
- GET /api/v1/scheduler/runs
