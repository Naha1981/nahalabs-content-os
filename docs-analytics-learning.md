# Analytics + Learning Engine v1.0

The analytics worker periodically pulls recent Zernio post analytics, maps provider post IDs back to NahaLabs publishing jobs, stores immutable metric snapshots, and derives lightweight business-level insights.

## Strategy feedback loop

`published asset -> metrics -> normalized snapshot -> insight -> next strategy context`

The domain owns the historical data. Zernio is only the analytics transport/provider.

## Current insight types

- `platform_performance`
- `winning_content`

These are intentionally conservative. More advanced models can later score hooks, formats, CTAs, topics, duration, retention curves, and posting windows once sufficient sample size exists.

## Worker

```bash
python -m app.workers.analytics_worker --once
```

Default loop interval is 15 minutes. In production, run it as an ECS/Fargate service or scheduled worker.

Zernio analytics availability varies by platform and account/plan; the worker treats provider failures as recoverable and keeps NahaLabs historical data intact. See the current Zernio API documentation for supported analytics endpoints and platform-specific capabilities.
