from pathlib import Path
import json

root = Path('.')

# Backend source fixes
p = root / 'backend/app/main.py'
s = p.read_text(encoding='utf-8')
assert 'from fastapi import FastAPI, UploadFile, File, HTTPException' in s
assert 'version="0.38.4"' in s
assert 'version": "0.38.3"' in s

s = s.replace(
    'from fastapi import FastAPI, UploadFile, File, HTTPException\n',
    'import os\nfrom fastapi import FastAPI, UploadFile, File, HTTPException\nfrom fastapi.responses import JSONResponse\n', 1)
marker = 'from .scheduler import list_scheduled_jobs, set_job_enabled, run_job, list_job_runs, automation_health\n'
assert marker in s
s = s.replace(marker, marker + 'from .browser_runtime import browser_worker_status, require_browser_worker, BrowserWorkerUnavailable\n', 1)

old_head = '''app = FastAPI(title="NahaLabs Reactivate API", version="0.38.4")
init_db()
MEDIA_DIR = Path(__import__("os").environ.get("REACTIVATE_MEDIA_DIR", str(Path(__file__).resolve().parent.parent / "media")))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "nahalabs-reactivate", "version": "0.38.3"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in __import__("os").environ.get("REACTIVATE_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Optional bearer-token protection for hosted environments. Health stays public.
_API_TOKEN = __import__("os").environ.get("REACTIVATE_API_TOKEN", "").strip()
'''
new_head = '''APP_VERSION = "0.38.5"

app = FastAPI(title="NahaLabs Reactivate API", version=APP_VERSION)
init_db()
MEDIA_DIR = Path(os.environ.get("REACTIVATE_MEDIA_DIR", str(Path(__file__).resolve().parent.parent / "media")))
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

_CORS_RAW = os.environ.get(
    "REACTIVATE_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5175,http://127.0.0.1:5175",
)
_CORS_ORIGINS = [o.strip().rstrip("/") for o in _CORS_RAW.split(",") if o.strip()]
_CORS_WILDCARD = "*" in _CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _CORS_WILDCARD else _CORS_ORIGINS,
    allow_credentials=not _CORS_WILDCARD,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health", tags=["ops"])
def health() -> dict:
    return {
        "status": "ok",
        "service": "nahalabs-reactivate",
        "version": APP_VERSION,
        "browser_worker": browser_worker_status(),
    }

# Optional bearer-token protection for hosted environments. Health stays public.
_API_TOKEN = os.environ.get("REACTIVATE_API_TOKEN", "").strip()
'''
assert old_head in s
s = s.replace(old_head, new_head, 1)

old_health = '''
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nahalabs-reactivate"}


'''
assert old_health in s
s = s.replace(old_health, '\n\n', 1)

guard = '''
def _discover_maps_guarded(query: str, location: str, limit: int, headless: bool) -> list[dict]:
    try:
        require_browser_worker()
    except BrowserWorkerUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    try:
        return discover_google_maps(query, location, limit, headless)
    except HTTPException:
        raise
    except NotImplementedError as exc:
        raise HTTPException(status_code=503, detail=(
            "The browser worker could not start a subprocess on this platform "
            f"({exc}). On Windows this means the Playwright event loop is not a "
            "ProactorEventLoop; restart the backend so the compatibility shim applies."
        ))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Google Maps discovery failed: {exc}")


'''
assert 'class ScoreResponse(BaseModel):' in s
s = s.replace('class ScoreResponse(BaseModel):\n', guard + 'class ScoreResponse(BaseModel):\n', 1)
s = s.replace(
    'businesses = discover_google_maps(request.query, request.location, request.limit, request.headless)',
    'businesses = _discover_maps_guarded(request.query, request.location, request.limit, request.headless)',
)
s = s.replace(
    'return outreach_summary(prospect_id, campaign_id, path=None) if False else {"prospect_id": prospect_id, "count": len(list_outreach_events(prospect_id, campaign_id, limit)), "events": list_outreach_events(prospect_id, campaign_id, limit)}',
    'events = list_outreach_events(prospect_id, campaign_id, limit)\n    return {"prospect_id": prospect_id, "count": len(events), "events": events}', 1,
)
assert '_sort_routes_by_specificity' not in s
s += '''


def _sort_routes_by_specificity() -> None:
    app.router.routes.sort(key=lambda route: getattr(route, "path", "").count("{"))


_sort_routes_by_specificity()
'''
p.write_text(s, encoding='utf-8')

# Browser worker probe
(root / 'backend/app/browser_runtime.py').write_text('''"""Hosted Playwright/Chromium availability probe."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


class BrowserWorkerUnavailable(RuntimeError):
    pass


_HINT = (
    "The Playwright Chromium browser is not available in this environment. "
    "Install it with `python -m playwright install --with-deps chromium`, "
    "or rebuild the container with INSTALL_PLAYWRIGHT=true."
)


@lru_cache(maxsize=1)
def _probe() -> dict:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception as exc:
        return {"available": False, "reason": f"playwright package not importable: {exc}"}
    override = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "").strip()
    roots = [Path(override)] if override and override != "0" else [
        Path.home() / ".cache" / "ms-playwright",
        Path.home() / "AppData" / "Local" / "ms-playwright",
        Path("/ms-playwright"),
    ]
    for root in roots:
        try:
            if root.is_dir() and any(root.glob("chromium*")):
                return {"available": True, "reason": "chromium present", "path": str(root)}
        except OSError:
            continue
    return {"available": False, "reason": "no chromium build found on disk"}


def browser_worker_status() -> dict:
    return _probe()


def require_browser_worker() -> None:
    status = _probe()
    if not status.get("available"):
        raise BrowserWorkerUnavailable(f"{_HINT} (detail: {status.get('reason')})")
''', encoding='utf-8')

# Render backend container
(root / 'Dockerfile').write_text('''FROM python:3.13-slim

ARG INSTALL_PLAYWRIGHT=true

ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PIP_NO_CACHE_DIR=1 \\
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \\
    REACTIVATE_DB_PATH=/app/data/reactivate.db \\
    REACTIVATE_MEDIA_DIR=/app/media

WORKDIR /app

RUN apt-get update \\
 && apt-get install -y --no-install-recommends ffmpeg espeak curl ca-certificates \\
 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

RUN if [ "$INSTALL_PLAYWRIGHT" = "true" ]; then \\
      python -m playwright install --with-deps chromium; \\
    else \\
      echo "Skipping Playwright browser install (INSTALL_PLAYWRIGHT=$INSTALL_PLAYWRIGHT)"; \\
    fi

COPY backend /app/backend
RUN mkdir -p /app/data /app/media

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \\
  CMD curl -fsS "http://127.0.0.1:${PORT:-8000}/health" || exit 1

CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'
''', encoding='utf-8')

# Render Blueprint: API + static frontend
(root / 'render.yaml').write_text('''services:
  - type: web
    name: nahalabs-reactivate-api
    runtime: docker
    plan: free
    region: frankfurt
    dockerfilePath: ./Dockerfile
    dockerContext: .
    healthCheckPath: /health
    autoDeploy: true
    envVars:
      - key: REACTIVATE_API_TOKEN
        generateValue: true
      - key: REACTIVATE_CORS_ORIGINS
        sync: false
      - key: REACTIVATE_DB_PATH
        value: /app/data/reactivate.db
      - key: REACTIVATE_MEDIA_DIR
        value: /app/media
      - key: PLAYWRIGHT_BROWSERS_PATH
        value: /ms-playwright
      - key: KIE_API_KEY
        sync: false
      - key: PYTHONUNBUFFERED
        value: "1"

  - type: web
    name: nahalabs-reactivate-web
    runtime: static
    plan: free
    rootDir: frontend
    buildCommand: npm ci && npm run build
    staticPublishPath: ./dist
    autoDeploy: true
    envVars:
      - key: VITE_API_BASE_URL
        fromService:
          type: web
          name: nahalabs-reactivate-api
          property: host
    headers:
      - path: /*
        name: X-Frame-Options
        value: SAMEORIGIN
      - path: /*
        name: X-Content-Type-Options
        value: nosniff
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
''', encoding='utf-8')

# Reproducible frontend dependencies
package = {
    "name": "nahalabs-reactivate-frontend",
    "private": True,
    "version": "0.38.5",
    "type": "module",
    "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
    "dependencies": {"react": "^18.3.1", "react-dom": "^18.3.1"},
    "devDependencies": {"@vitejs/plugin-react": "^4.7.0", "vite": "^5.4.21"},
}
(root / 'frontend/package.json').write_text(json.dumps(package, indent=2) + chr(10), encoding='utf-8')

(root / 'frontend/vite.config.js').write_text('''import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const BACKEND = process.env.VITE_DEV_BACKEND || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: 'localhost',
    port: 5175,
    proxy: {
      '/api': { target: BACKEND, changeOrigin: true },
      '/media': { target: BACKEND, changeOrigin: true },
      '/health': { target: BACKEND, changeOrigin: true },
    },
  },
  build: { outDir: 'dist', sourcemap: false },
});
''', encoding='utf-8')

(root / 'frontend/index.html').write_text('''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NahaLabs Reactivate</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
''', encoding='utf-8')

# Frontend API base + live API version
p = root / 'frontend/src/main.jsx'
s = p.read_text(encoding='utf-8')
assert "const API = '/api';" in s
assert ' / v0.38.5' in s
assert 'const [automation, setAutomation] = useState(null);' in s
needle = "useEffect(()=>{const h=e=>openWorkspace(e.detail);window.addEventListener('open-prospect-workspace',h);return()=>window.removeEventListener('open-prospect-workspace',h)},[]);"
assert needle in s
s = s.replace(
    "const API = '/api';",
    "function resolveApiBase(raw) {\n  let base = (raw || '').trim().replace(/\\/+$/, '');\n  if (!base) return '';\n  if (!/^https?:\\/\\//i.test(base)) base = `https://${base}`;\n  return base.replace(/\\/api$/i, '');\n}\n\nconst API = resolveApiBase(import.meta.env.VITE_API_BASE_URL);",
    1,
)
s = s.replace(
    "  const [automation, setAutomation] = useState(null);",
    "  const [automation, setAutomation] = useState(null);\n  const [apiVersion, setApiVersion] = useState('…');",
    1,
)
s = s.replace(
    needle,
    "useEffect(()=>{let live=true;fetch(`${API}/health`).then(r=>r.json()).then(d=>{if(live)setApiVersion(d.version||'unknown')}).catch(()=>{if(live)setApiVersion('offline')});return()=>{live=false}},[]);\n" + needle,
    1,
)
s = s.replace(' / v0.38.5', ' / v{apiVersion}', 1)
p.write_text(s, encoding='utf-8')

(root / '.gitignore').write_text('''.env
.env.*
!.env.example
*.db
*.sqlite
*.sqlite3
.pytest_cache/
.venv/
__pycache__/
dist/
frontend/dist/
frontend/node_modules/
node_modules/
''', encoding='utf-8')

(root / 'docs/DEPLOY-RENDER.md').write_text('''# NahaLabs Reactivate — Render deployment\n\nThis Blueprint deploys two free Render services:\n\n- `nahalabs-reactivate-api`: FastAPI Docker web service\n- `nahalabs-reactivate-web`: Vite/React static site\n\nThe API listens on Render's `$PORT`, exposes `/health`, `/api/v1/*`, and `/media/*`, and reports Playwright/Chromium availability from `/health`.\n\nThe static frontend reads `VITE_API_BASE_URL` at build time. Render supplies the API hostname through `fromService`; the frontend adds `https://` when necessary and never appends `/api`.\n\nAfter the first Blueprint deploy, set the API service's `REACTIVATE_CORS_ORIGINS` to the exact static site URL and redeploy the API.\n\nThe free filesystem is ephemeral, so SQLite and generated media are disposable until storage is migrated to an external database/object store or a plan with persistent storage.\n''', encoding='utf-8')

print('Render source migration complete')
