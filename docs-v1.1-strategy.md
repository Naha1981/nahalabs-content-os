# NahaLabs Content OS v1.1 — Adaptive Strategy

v1.1 closes the loop between published content and the next content pack.

## What changed
- Fixed the analytics dependency alias (`get_current_user`).
- Added `ContentExperiment` persistence for explicit A/B-style hypotheses.
- Added `StrategyContext` combining Business + Brand DNA + normalized historical performance.
- Uses the latest metric snapshot per publishing job so repeated analytics captures do not inflate sample size.
- Requires a minimum of 5 measured posts before a content type can be treated as a validated winner.
- Added strategy context and experiment APIs.
- Keeps approval as a hard boundary: performance signals influence recommendations; they never authorize publishing.

## Endpoints
- `GET /api/v1/strategy/businesses/{business_id}/context`
- `POST /api/v1/strategy/businesses/{business_id}/experiments`
- `GET /api/v1/strategy/businesses/{business_id}/experiments`
- `POST /api/v1/strategy/experiments/{experiment_id}/start`

## Next step
v1.2 should attach explicit experiment IDs/variables to CreativeBrief and PublishingJob metadata, then calculate experiment winners only after the configured minimum sample size and a statistically defensible confidence threshold.
