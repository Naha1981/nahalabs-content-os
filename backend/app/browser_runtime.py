"""Hosted Playwright/Chromium availability probe."""

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
