# Reactivate v0.36 — Autonomous Worker

## Goal
Turn the persisted scheduler into an actual background worker that evaluates due jobs and executes them without requiring the UI to be open.

## Scope
- Pure-Python cron matching for Reactivate's five-field schedules.
- Calculate and persist the next scheduled run.
- Background worker loop with configurable polling interval.
- `--once` mode for Windows Task Scheduler/Trigger.dev/container orchestration.
- Prevent duplicate execution within the same minute.
- Preserve existing safety gates: no fake external discovery, no automatic outbound outreach, publishing remains credential/provider gated.

## Run
`python -m backend.app.worker --once`

Continuous local worker:
`python -m backend.app.worker --interval 30`
