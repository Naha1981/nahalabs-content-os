# NahaLabs Reactivate v0.38 — Production Hosting Layer

## Objective
Give Reactivate a repeatable containerised deployment target with health checks, configurable paths, CORS, and optional bearer authentication.

## Acceptance criteria
1. Backend builds from Dockerfile.
2. `/health` is public and reports service/version.
3. API can be protected by `REACTIVATE_API_TOKEN`.
4. DB/media paths are configurable by environment variables.
5. Render blueprint exists with health check.
6. Trigger.dev can call protected scheduler endpoints using the same bearer token.
7. Documentation explicitly warns that free Render filesystem is ephemeral.


## Windows compatibility
The production-hosting layer must remain Windows-safe during local development: timezone data is explicit and SQLite connections are closed deterministically to avoid Windows file locking.
