# Reactivate v0.38

Production Hosting Layer for the NahaLabs Reactivate backend.

- Dockerised FastAPI API
- Render deployment blueprint
- Public `/health` endpoint
- Optional bearer-token protection
- Configurable DB/media paths
- Trigger.dev-compatible HTTPS architecture

The current SQLite/media layer is not durable on a free ephemeral host. Persistent database/storage is deliberately the next infrastructure phase.


## Windows note
Install FFmpeg and eSpeak and keep `tzdata` installed for `Africa/Johannesburg` timezone support. SQLite connections are explicitly closed for Windows file-handle compatibility.
