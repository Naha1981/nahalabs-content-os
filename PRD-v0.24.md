# NahaLabs Reactivate v0.24 — Performance & Learning Engine

## Goal
Close the loop after publishing by storing observed performance and turning it into transparent, non-causal learning signals.

## Scope
- Performance observation storage per publishing job.
- Metrics: impressions, views, likes, comments, shares, saves, clicks, leads, conversions, revenue.
- Derived engagement, click, lead and conversion rates.
- Prospect-level performance endpoint.
- Prospect-level learning summary.
- Global learning summary.
- No platform API credentials required: manual/provider observations are supported.

## Guardrails
- Observed data is separated from inferred learning.
- No unsupported ROI or causal claims.
- Empty data state is explicit.
- Real platform analytics adapters remain a future provider layer.
