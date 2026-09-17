# Reactivate v0.38.4 — Windows Playwright Runtime Fix

## Problem
The FastAPI Radar endpoint executes synchronous Playwright inside an AnyIO worker thread. On Windows that thread can use a SelectorEventLoop, which does not support subprocess creation required by Playwright.

## Change
Add a small Windows compatibility helper that installs a ProactorEventLoop in the worker thread before calling Playwright sync API, then cleans it up after the worker finishes. Apply the helper to Google Maps discovery and social browser collection.

## Acceptance
- Existing regression suite remains green.
- Live Radar no longer fails at `asyncio.create_subprocess_exec` with `NotImplementedError` on supported Windows setups.
- No change to evidence, scoring, or public-data boundaries.
