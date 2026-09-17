# NahaLabs Reactivate v0.37 — Trigger.dev Deployment Layer

## Goal
Move recurring Reactivate execution from a laptop/local worker into a hosted Trigger.dev scheduler while keeping Reactivate's existing FastAPI scheduler as the source of job definitions and execution logic.

## Architecture
Trigger.dev durable cron → Reactivate FastAPI scheduler endpoint → existing job logic → SQLite/Postgres-backed state → Control Center.

Trigger.dev owns hosted timing/retries/observability. Reactivate owns business logic and safety gates.

## Schedules
All six existing jobs are declared in `trigger/reactivate-schedules.ts` using `Africa/Johannesburg` timezone.

## Safety
- No fake external discovery.
- No automatic outbound outreach.
- Publishing remains provider/credential gated.
- Trigger tasks fail loudly when the Reactivate API is unavailable.
- Disabled Reactivate jobs are skipped.
- No Trigger secret is committed to the repository.

## Deployment prerequisites
1. A publicly reachable HTTPS Reactivate API.
2. Trigger.dev project ref.
3. `TRIGGER_SECRET_KEY` configured through Trigger.dev.
4. `REACTIVATE_API_URL` configured through Trigger.dev.
5. Optional shared `REACTIVATE_API_TOKEN` if API authentication is enabled.

## Local development
From `trigger/`:

```bash
npm install
npm run dev
```

Replace `YOUR_TRIGGER_PROJECT_REF` in `trigger.config.ts` before deployment.

## Production
```bash
npx trigger.dev@latest deploy
```

This version prepares the integration; it does not claim that a Trigger.dev project has been created or deployed.
