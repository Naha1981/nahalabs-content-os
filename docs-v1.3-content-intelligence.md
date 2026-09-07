# NahaLabs Content OS v1.3 — Content Intelligence Engine

## Purpose
Turn measured performance + Brand DNA into the next 10–50 creative briefs.

## Flow
Analytics → Strategy Context → Evidence ranking → Exploitation + diversification → Experiment assignment → Creative briefs → Generation → Approval → Publishing → Measurement.

## API
- `POST /api/v1/content-intelligence/businesses/{business_id}/plan`
- `GET /api/v1/content-intelligence/businesses/{business_id}/preview`

## Guardrails
- Validated content winners require the existing minimum sample size.
- A winner is a ranking signal, not automatic publishing permission.
- Social proof cannot be fabricated.
- Source footage remains the default creative anchor.
- Higgsfield is conditional final polish, not mandatory generation.
- All generated briefs still require the normal approval boundary before publishing.

## Strategy metadata
Each generated ContentPack and CreativeBrief records the evidence sample, winning pattern, platform priority and experiment assignment in JSONB for auditability and downstream workers.
