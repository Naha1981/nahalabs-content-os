# NahaLabs Reactivate v0.27 — Prospect-to-Campaign Automation

## Objective
Connect seller-owned prospect qualification directly to a guarded reactivation campaign launch.

## Flow
Qualified prospect → Launch Reactivation → generate evidence-aware content using learning signals → create campaign → human approval → production → publishing → measurement.

## Guardrails
- Only `QUALIFIED` prospects may use the automated launch endpoint.
- Do not create a second active campaign for the same prospect.
- Human approval remains required before production/publishing.
- Live social publishing remains credential-gated.
- No invented performance or evidence.

## API
`POST /api/v1/prospects/{prospect_id}/campaigns/auto`

Returns the campaign, generated assets and learning context when created; returns the existing active campaign when a duplicate is attempted.
