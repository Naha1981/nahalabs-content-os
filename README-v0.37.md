# NahaLabs Reactivate v0.37

v0.37 adds a Trigger.dev deployment layer for the six Reactivate automations.

Trigger.dev provides hosted durable cron scheduling and task observability; the existing Reactivate FastAPI service remains responsible for executing business logic. The six schedules are declared in code and use `Africa/Johannesburg`.

See `PRD-v0.37.md` for deployment prerequisites and `trigger/` for the integration.

Important: no hosted Trigger.dev project is created by this archive. Add the project ref and secrets, then deploy.
