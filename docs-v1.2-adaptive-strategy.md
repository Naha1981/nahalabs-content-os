# NahaLabs Content OS v1.2 — Adaptive Strategy

## Purpose
Turn analytics into controlled creative decisions without allowing the model to silently publish.

## Loop
Published content → normalized metrics → latest-post snapshots → evidence thresholds → adaptive plan → experiment assignment → new creative brief → approval → publishing → measurement.

## API
- `GET /api/v1/strategy/businesses/{business_id}/adaptive-plan`
- `GET /api/v1/strategy/businesses/{business_id}/experiments/{experiment_id}/assignment?sequence_number=0`

## Guardrails
- A content type needs at least 5 measured posts before being called a validated winner.
- Experiment assignment is deterministic for reproducibility.
- Strategy is a ranking/recommendation layer, never publishing authority.
- Publishing still requires explicit approval grants.
- Historical analytics remain stored in NahaLabs; provider APIs are transport/sync sources.

## Zernio integration note
Zernio currently exposes analytics endpoints including general post analytics, best-time, content-decay, daily metrics, post timeline, and posting-frequency. These should be pulled through the adapter and cached locally rather than fanned out on every dashboard request.

## Compatibility fix
SQLAlchemy reserves the declarative attribute name `metadata`. JSON columns that were previously exposed through that Python attribute are now mapped through non-reserved Python names while retaining the existing database column name `metadata`.
