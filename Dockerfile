FROM python:3.13-slim

ARG INSTALL_PLAYWRIGHT=true

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    REACTIVATE_DB_PATH=/app/data/reactivate.db \
    REACTIVATE_MEDIA_DIR=/app/media

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg espeak curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

RUN if [ "$INSTALL_PLAYWRIGHT" = "true" ]; then \
      python -m playwright install --with-deps chromium; \
    else \
      echo "Skipping Playwright browser install (INSTALL_PLAYWRIGHT=$INSTALL_PLAYWRIGHT)"; \
    fi

COPY backend /app/backend
RUN mkdir -p /app/data /app/media

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT:-8000}/health" || exit 1

CMD uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'
