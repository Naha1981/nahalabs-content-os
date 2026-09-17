# Reactivate v0.28 — Campaign Command Center

## Goal
Create one operational view for campaign execution across prospects, approvals, production, publishing, measurement and blockers.

## Scope
- Global campaign command-center API.
- Join campaign records to prospect identity, qualification and score.
- Surface stage/status, blockers and next action.
- Surface counts for content, production, publishing and performance observations.
- Dashboard UI with active/blocked/completed summary and campaign worklist.

## Guardrails
- No fabricated platform state.
- Live publishing remains credential-gated.
- Campaign state comes from persisted records.
