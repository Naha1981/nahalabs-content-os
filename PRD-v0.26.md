# Reactivate v0.26 — Autonomous Reactivation Campaigns

## Goal
Turn a qualified prospect into an orchestrated campaign while preserving human approval and credential gates.

## Flow
Plan → generate content → human approval → production → publishing package → measurement → learning.

## Safety gates
- Generated content is never silently approved.
- Verified facts remain required for factual claims.
- Live social publishing is never simulated as real publishing.
- Provider credentials remain server-side and external-platform actions are gated.

## Acceptance criteria
1. Campaign is persisted against a prospect.
2. Campaign creates a bounded content set using current learning signals.
3. Campaign exposes blockers and next action.
4. Approved assets can advance into production jobs.
5. Rendered production can advance toward publishing.
6. Publishing and measurement remain separate operational stages.
7. Learning remains the feedback loop for the next iteration.
