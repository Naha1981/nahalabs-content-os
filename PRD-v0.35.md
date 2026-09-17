# NahaLabs Reactivate v0.35 — Automation Control Center

## Goal
Provide one control surface for scheduled automation jobs, execution health, enable/disable controls, and safe manual execution.

## Scope
- Scheduler health endpoint
- Automation Control Center UI
- Job enable/disable
- Run Now
- Last-run state and execution health
- Preserve provider/network gating

## Safety
No external publishing, messaging, or discovery is fabricated. Existing scheduler provider gates remain authoritative.
