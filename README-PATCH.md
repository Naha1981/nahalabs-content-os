# Reactivate local frontend patch v0.38.5

Apply this patch to the existing `nahalabs-reactivate-v0.38.3` folder. It changes browser API calls from direct `127.0.0.1:8000` requests to same-origin `/api` requests and adds a Vite proxy to the FastAPI backend. It does not touch the backend, database, or virtual environment.
