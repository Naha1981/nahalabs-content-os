from __future__ import annotations

import asyncio
import sys


def prepare_sync_playwright_event_loop():
    """Ensure Playwright's sync API has a subprocess-capable loop on Windows.

    FastAPI/AnyIO may execute synchronous endpoint code inside a worker thread.
    On Windows that thread can otherwise end up with a SelectorEventLoop, which
    cannot launch subprocesses. Playwright requires ProactorEventLoop there.

    Returns the loop created by this helper (if any) so callers can close it.
    """
    if sys.platform != "win32":
        return None

    try:
        current = asyncio.get_event_loop()
    except RuntimeError:
        current = None

    if current is not None and not isinstance(current, asyncio.SelectorEventLoop):
        return None

    proactor_type = getattr(asyncio, "ProactorEventLoop", None)
    if proactor_type is None:
        return None

    loop = proactor_type()
    asyncio.set_event_loop(loop)
    return loop


def cleanup_sync_playwright_event_loop(loop) -> None:
    if loop is None:
        return
    try:
        if not loop.is_closed():
            loop.close()
    finally:
        try:
            asyncio.set_event_loop(None)
        except Exception:
            pass
